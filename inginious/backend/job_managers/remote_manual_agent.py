# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" A JobManager that can interact with distant agents, via RPyC """
import socket

import threading
import copy
import tempfile
import tarfile
from StringIO import StringIO
import re
import os

import rpyc
from rpyc import BgServingThread

from inginious.backend.job_managers.abstract import AbstractJobManager
from inginious.common.base import directory_compare_from_hash, directory_content_with_hash, hash_file
import inginious.common.custom_yaml


class RemoteManualAgentJobManager(AbstractJobManager):
    """
        A Job Manager that handles connections with distant Agents using RPyC.
        This job manager makes the assumption that everything is configured correctly on all agents; all remote docker have the same version of the
        container images, etc.
    """

    def __init__(self, agents, image_aliases, task_directory, course_factory, task_factory, hook_manager=None, is_testing=False):
        """
            Starts the job manager.

            Arguments:

            :param agents:
                A list of dictionaries containing information about distant inginious.backend agents:
                ::

                    {
                        'host': "the host of the agent",
                        'port': "the port on which the agent listens"
                        'ssh_port': "the port on which the interface for accessing the debug ssh server is accessible (not mandatory, can be None)"
                    }

                If a least one ssh_port is absent or None, remote debugging will be deactivated for all agents
            :param task_directory: the task directory
            :param course_factory: a CourseFactory object
            :param task_factory: a TaskFactory object, possibly with specific task files managers attached
            :param image_aliases: a dict of image aliases, like {"default": "ingi/inginious-c-default"}.
            :param hook_manager: An instance of HookManager. If no instance is given(None), a new one will be created.
        """

        AbstractJobManager.__init__(self, image_aliases, hook_manager, is_testing)

        self._task_directory = task_directory

        self._agents = [None for _ in range(0, len(agents))]
        self._agents_thread = [None for _ in range(0, len(agents))]
        self._agents_info = agents

        self._course_factory = course_factory
        self._task_factory = task_factory

        self._next_agent = 0
        self._running_on_agent = [[] for _ in range(0, len(agents))]

        self._last_content_in_task_directory = None

        self._timers = {}

        # Is remote debugging activated?
        nb_ok = 0
        message = "ok"

        for info in self._agents_info:
            if info.get('ssh_port') is not None:
                nb_ok += 1
            elif nb_ok != 0:
                nb_ok = -1
                message = "one_error"

        if nb_ok == 0:
            self._remote_debugging_activated = False
            print "Remote debugging is deactivated as all agent have no ssh_port defined"
        elif nb_ok == -1:
            self._remote_debugging_activated = False
            print "Remote debugging is deactivated as one agent has no ssh_port defined"
        else:
            self._remote_debugging_activated = True

    def start(self):
        # init the synchronization of task directories
        self._last_content_in_task_directory = directory_content_with_hash(self._task_directory)
        self._timers[self._try_synchronize_task_dir] = threading.Timer((30 if not self._is_testing else 2), self._try_synchronize_task_dir)
        self._timers[self._try_synchronize_task_dir].start()

        # connect to agents
        self._try_agent_connection()

    def _try_agent_connection(self):
        """ Tries to connect to the agents that are not connected yet """
        if self._closed:
            return

        for entry, info in enumerate(self._agents_info):
            if self._agents[entry] is None:
                try:
                    conn = rpyc.connect(info['host'], info['port'], service=self._get_rpyc_server(entry),
                                        config={"allow_public_attrs": True, 'allow_pickle': True})
                    # Try to access conn.root. This raises an exception when the remote RPyC is not yet fully initialized
                    if not conn.root:
                        raise Exception("Cannot get remote service")
                except:
                    self._agents[entry] = None
                    self._agents_thread[entry] = None
                    print "Cannot connect to agent {}-{}".format(info['host'], info['port'])
                else:
                    self._agents[entry] = conn
                    self._agents_thread[entry] = BgServingThread(conn)
                    self._synchronize_image_aliases(self._agents[entry])
                    self._synchronize_task_dir(self._agents[entry])

        if not self._is_testing:
            self._timers[self._try_agent_connection] = threading.Timer(10, self._try_agent_connection)
            self._timers[self._try_agent_connection].start()

    def _synchronize_image_aliases(self, agent):
        """ Update the list of image aliases on the remote agent """
        update_image_aliases = rpyc.async(agent.root.update_image_aliases)
        update_image_aliases(self._image_aliases).wait()

    def _try_synchronize_task_dir(self):
        """ Check if the remote tasks dirs (on the remote agents) should be updated """
        if self._closed:
            return

        current_content_in_task_directory = directory_content_with_hash(self._task_directory)
        changed, deleted = directory_compare_from_hash(current_content_in_task_directory, self._last_content_in_task_directory)
        if len(changed) != 0 or len(deleted) != 0:
            self._last_content_in_task_directory = current_content_in_task_directory
            for agent in self._agents:
                if agent is not None:
                    self._synchronize_task_dir(agent)

        if not self._is_testing:
            self._timers[self._try_synchronize_task_dir] = threading.Timer(30, self._try_synchronize_task_dir)
            self._timers[self._try_synchronize_task_dir].start()

    def _synchronize_task_dir(self, agent):
        """ Synchronizes the task directory with the remote agent. Steps are:
            - Get list of (path, file hash) for the main task directory (p1)
            - Ask agent for a list of all files in their task directory (p1)
            - Find differences for each agents (p2)
            - Create an archive with differences (p2)
            - Send it to each agent (p2)
            - Agents updates their directory
        """
        local_td = self._last_content_in_task_directory

        # As agent only supports task.yaml files as descriptors (and not exotic things like task.rst...), we have to ensure that we convert and send
        # task.yaml files to it.
        task_files_to_convert = ["task." + ext for ext in self._task_factory.get_available_task_file_extensions()]
        task_files_to_convert.remove("task.yaml")

        new_local_td = {}
        generated_yaml_content = {}
        for file_path, data in local_td.iteritems():
            match = re.match(r'^([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)/(task.[a-z0-9]+)$', file_path)
            if match is not None and match.group(3) in task_files_to_convert:
                try:
                    path_to_file, _ = os.path.split(file_path)
                    courseid, taskid = match.group(1), match.group(2)
                    content = self._task_factory.get_task_descriptor_content(courseid, taskid)
                    yaml_content = StringIO(inginious.common.custom_yaml.dump(content).encode('utf-8'))
                    new_local_td[os.path.join(path_to_file, "task.yaml")] = (hash_file(yaml_content), 0o777)
                    yaml_content.seek(0)
                    generated_yaml_content[os.path.join(path_to_file, "task.yaml")] = yaml_content
                except:
                    print "Cannot convert {} to a yaml file for the agent!".format(file_path)
                    new_local_td[file_path] = data
            else:
                new_local_td[file_path] = data

        async_get_file_list = rpyc.async(agent.root.get_task_directory_hashes)
        async_get_file_list().add_callback(lambda r: self._synchronize_task_dir_p2(agent, new_local_td, generated_yaml_content, r))

    def _synchronize_task_dir_p2(self, agent, local_td, generated_files, async_value_remote_td):
        """ Synchronizes the task directory with the remote agent, part 2 """
        try:
            remote_td = copy.deepcopy(async_value_remote_td.value)
        except:
            print "An error occured while retrieving list of files in the task dir from remote agent"
            return

        if remote_td is None:  # sync disabled for this Agent
            return

        to_update, to_delete = directory_compare_from_hash(local_td, remote_td)
        tmpfile = tempfile.TemporaryFile()
        tar = tarfile.open(fileobj=tmpfile, mode='w:gz')
        for path in to_update:
            # be a little safe about what the agent returns...
            if os.path.relpath(os.path.join(self._task_directory, path), self._task_directory) == path and ".." not in path:
                if path in generated_files:  # the file do not really exists on disk, it was generated
                    info = tarfile.TarInfo(name=path)
                    info.size = generated_files[path].len
                    info.mode = 0o777
                    tar.addfile(tarinfo=info, fileobj=generated_files[path])
                else:  # the file really exists on disk
                    tar.add(arcname=path, name=os.path.join(self._task_directory, path))
            else:
                print "Agent returned non-safe file path: " + path
        tar.close()
        tmpfile.flush()
        tmpfile.seek(0)

        # sync the agent
        async_update = rpyc.async(agent.root.update_task_directory)
        # do not forget to close the file
        async_update(tmpfile, to_delete).add_callback(lambda r: self._synchronize_task_dir_done(agent, tmpfile))

    def _synchronize_task_dir_done(self, agent, file_to_close):
        """ Ends the file sync by warning hooks and closing some files """
        file_to_close.close()
        self._hook_manager.call_hook("job_manager_agent_sync_done", agent=agent)

    def _select_agent(self):
        """ Select which agent should handle the next job.
            For now we use a round-robin, but will probably be improved over time.
        """
        available_agents = [i for i, j in enumerate(self._agents) if j is not None]
        if len(available_agents) == 0:
            return None
        chosen_agent = available_agents[self._next_agent % len(available_agents)]
        self._next_agent += 1
        return chosen_agent

    def _execute_job(self, jobid, task, inputdata, debug):
        """ Chooses an agent and executes a job on it """
        agent_id = self._select_agent()
        if agent_id is None:
            self._agent_job_ended(jobid,
                                  {'result': 'crash',
                                   'text': 'There are not any agent available for grading. Please retry later. '
                                           'If this error persists, please contact the course administrator.'},
                                  None)
            return
        try:
            agent = self._agents[agent_id]
            async_run = rpyc.async(agent.root.new_job)
            self._running_on_agent[agent_id].append(jobid)
            async_run(str(jobid), str(task.get_course_id()), str(task.get_id()), dict(inputdata), debug,
                      (lambda distant_conn_id, ssh_key: self._handle_ssh_callback(jobid, distant_conn_id, ssh_key)),
                      (lambda r: self._execute_job_callback(jobid, r, agent_id)))
        except:
            self._agent_shutdown(agent_id)
            self._execute_job(jobid, task, inputdata, debug)

    def _execute_batch_job(self, jobid, container_name, inputdata):
        """ Chooses an agent and executes a job on it """

        # Compress inputdata before sending it to the agent
        tmpfile = tempfile.TemporaryFile()
        tar = tarfile.open(fileobj=tmpfile, mode='w:gz')
        for key, val in inputdata.iteritems():
            info = tarfile.TarInfo(name=key)
            info.mode = 0o777
            if isinstance(val, basestring):
                fileobj = StringIO(val)
                info.size = fileobj.len
                tar.addfile(tarinfo=info, fileobj=fileobj)
            else:
                fileobj = val
                fileobj.seek(0, 2)
                info.size = fileobj.tell()
                fileobj.seek(0)
                tar.addfile(tarinfo=info, fileobj=fileobj)
        tar.close()
        tmpfile.seek(0)

        agent_id = self._select_agent()
        if agent_id is None:
            self._agent_batch_job_ended(jobid,
                                        {'retval': -1,
                                         'stderr': 'There are not any agent available for running this job. '
                                                   'Please retry later. If this error persists, please contact the course administrator.'},
                                        None)
            return

        try:
            agent = self._agents[agent_id]
            async_run = rpyc.async(agent.root.new_batch_job)
            self._running_on_agent[agent_id].append(jobid)
            async_run(str(jobid), str(container_name), tmpfile, lambda r: self._execute_batch_job_callback(jobid, r, agent_id))
        except:
            self._agent_shutdown(agent_id)
            self._execute_batch_job(jobid, container_name, inputdata)

    def _get_batch_container_metadata_from_agent(self, container_name):
        agent_id = self._select_agent()
        if agent_id is None:
            return (None, None, None)
        try:
            agent = self._agents[agent_id]
            async_run = rpyc.async(agent.root.get_batch_container_metadata)
            result = async_run(str(container_name))
            result.wait()
            return copy.deepcopy(result.value)
        except:
            return (None, None, None)

    def _agent_job_ended(self, jobid, result, agent_id=None):
        """ Custom _job_ended with more infos """
        if agent_id is not None:
            self._running_on_agent[agent_id].remove(jobid)
        AbstractJobManager._job_ended(self, jobid, result)

    def _agent_batch_job_ended(self, jobid, result, agent_id=None):
        """ Custom _job_ended with more infos """
        if agent_id is not None:
            self._running_on_agent[agent_id].remove(jobid)
        AbstractJobManager._batch_job_ended(self, jobid, result)

    def _execute_job_callback(self, jobid, callback_return_val, agent_id):
        """ Called when an agent is done with a job or raised an exception """
        self._agent_job_ended(jobid, copy.deepcopy(callback_return_val), agent_id)

    def _execute_batch_job_callback(self, jobid, val, agent_id):
        """ Called when an agent is done with a job or raised an exception """
        if "file" in val:
            f = val["file"]
            del val["file"]
            val = copy.deepcopy(val)
            tmpfile = tempfile.TemporaryFile()
            tmpfile.write(f.read())
            tmpfile.seek(0)
            val["file"] = tmpfile
        else:
            val = copy.deepcopy(val)
        self._agent_batch_job_ended(jobid, val, agent_id)

    def _get_rpyc_server(self, agent_id):
        """ Return a service associated with this JobManager instance """
        on_agent_connection = self._on_agent_connection
        on_agent_disconnection = self._on_agent_disconnection

        class MasterBackendServer(rpyc.Service):
            def on_connect(self):
                on_agent_connection()

            def on_disconnect(self):
                on_agent_disconnection(agent_id)

        return MasterBackendServer

    def _on_agent_connection(self):
        """ Called when a RPyC service start: handles the connection of a distant Agent """
        print "Agent connected"

    def _on_agent_disconnection(self, agent_id):
        """ Called when a RPyC service ends: handles the disconnection of a distant Agent """
        print "Agent disconnected"
        self._agent_shutdown(agent_id)

    def _agent_shutdown(self, agent_id):
        """ Close a connection to an agent (failure/...) """

        # delete jobs that were running on this agent
        for jid in self._running_on_agent[agent_id]:
            self._agent_job_ended(jid, {'result': 'crash', 'text': 'Remote agent shutdown'}, agent_id)

        agent_conn = self._agents[agent_id]
        bg_thread = self._agents_thread[agent_id]

        self._agents[agent_id] = None
        self._running_on_agent[agent_id] = []
        self._agents_thread[agent_id] = None

        try:
            if agent_conn is not None:
                agent_conn.close()
        except:
            pass

        try:
            if bg_thread is not None:
                bg_thread.close()
        except:
            pass

    def number_agents_available(self):
        """ Returns the number of connected agents """
        return len([entry for entry in self._agents if entry is not None])

    def close(self):
        """ Close the Job Manager """
        self._closed = True
        for i, entry in enumerate(self._agents):
            if entry is not None:
                # Hack a bit BgServingThread to ensure it closes properly
                thread = self._agents_thread[i]
                thread._active = False  # pylint: disable=W0212
                self._agents[i] = None
                self._agents_thread[i] = None
                entry.close()
                thread._thread.join()  # pylint: disable=W0212
                thread._conn = None  # pylint: disable=W0212
        for f in self._timers:
            self._timers[f].cancel()

    def is_remote_debug_active(self):
        return self._remote_debugging_activated

    def get_socket_to_debug_ssh(self, job_id):
        if not self._remote_debugging_activated:
            raise Exception("Remote debugging is not activated")

        remote_conn_id = self._get_distant_conn_id_for_job(job_id)
        if remote_conn_id is None:
            return None
        remote_agent_id = None
        for agent_id, running_jids in enumerate(self._running_on_agent):
            if job_id in running_jids:
                remote_agent_id = agent_id
                break
        if remote_agent_id is None:
            return None

        client = socket.create_connection((self._agents_info[remote_agent_id]["host"], self._agents_info[remote_agent_id]["ssh_port"]))
        client.send(remote_conn_id + "\n")
        retval = ""
        while retval not in ["ok\n", "ko\n"]:
            retval += client.recv(3)
        retval = retval.strip()
        if retval != "ok":
            client.close()
            return None
        return client
