# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" Agent, managing docker """

import copy
import json
import logging
import os.path
from shutil import rmtree
import thread

import docker
import rpyc
from rpyc.utils.server import ThreadedServer

from backend_agent.cgroup_helper import CGroupTimeoutWatcher
import common.base
from common.courses import Course


class StudentContainerManagementService(rpyc.Service):

    def on_connect(self):
        """ Handles connection of a grading container """
        self.client_addr, _ = self._conn._config['endpoints'][1]

    def on_disconnect(self):
        """ Handles disconnection of a grading container"""
        pass

    def exposed_run(self, container_name, memory_limit, time_limit, debug, callback):
        """ Creates a new container for a grading container.
            ```container_name``` is the container to start (using the name of the alias list),
            ```memory_limit``` is the memory limit in Mo,
            ```time_limit``` is the maximum CPU time used in seconds,
            ```debug``` a boolean indicating if the task should run in debug mode or not
            ```callback``` is a function that will be called with the following arguments:
            * ```host```, the hostname/address of the new container
            * ```port```, the port on which the SSH server of the new container listens

            This function will start the container, then call the callback.
            When the callback ends, this functions will close and delete the content of the new container.
        """
        pass


class Agent(object):

    def __init__(self, master_port, image_aliases, task_folder="./tasks", docker_url="172.16.42.43:4243", tmp_dir="./agent_tmp", cgroup_location="/sys/fs/cgroups"):
        logging.info("Starting agent")
        self.image_aliases = image_aliases
        common.base.init_common_lib(task_folder, [], 1)  # we do not need to upload file, so not needed here
        self.task_folder = task_folder
        self.cgroup_location = cgroup_location
        self.docker_url = docker_url
        self.tmp_dir = tmp_dir

        try:
            os.mkdir(tmp_dir)
        except:
            pass

        print "Start cgroup helper"
        self._timeout_watcher = CGroupTimeoutWatcher(docker_url)
        self._timeout_watcher.start()

        print "Starting RPyC server - backend connection"
        self._backend_server = ThreadedServer(self._get_agent_backend_service(), port=master_port, protocol_config={"allow_public_attrs": True, 'allow_pickle': True})
        self._backend_server.start()

    def handle_job(self, job_id, course_id, task_id, inputdata, debug, _):
        print "Received request for jobid {}".format(job_id)

        # Deepcopy inputdata (to bypass "passage by reference" of RPyC)
        inputdata = copy.deepcopy(inputdata)

        # Initialize connection to Docker
        try:
            docker_connection = docker.Client(base_url=self.docker_url, version="1.14")
        except:
            print "Cannot connect to Docker!"
            return {'result': 'crash', 'text': 'Cannot connect to Docker'}

        # Get back the task data (for the limits)
        try:
            task = Course(course_id).get_task(task_id)
        except:
            print "Task unavailable on this agent!"
            return {'result': 'crash', 'text': 'Task unavailable on agent. Please contact your course administrator.'}

        limits = task.get_limits()

        mem_limit = limits.get("memory", 100)
        if mem_limit < 20:
            mem_limit = 20

        environment = task.get_environment()
        if environment not in self.image_aliases:
            print "Unknown environment {} (not in aliases)".format(environment)
            return {'result': 'crash', 'text': 'Unknown container. Please contact your course administrator.'}
        environment = self.image_aliases[environment]

        # Run the container
        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                network_disabled=True,
                volumes={'/ro/task': {}, '/sockets': {}, '/student': {}},
                mem_limit=(mem_limit + 10) * 1024 * 1024  # add 10 mo of bonus, as we check the memory in the "cgroup" thread
            )
            container_id = response["Id"]

            # Make the needed directories
            container_path = os.path.join(self.tmp_dir, container_id)
            sockets_path = os.path.join(self.tmp_dir, container_id, 'sockets')
            student_path = os.path.join(self.tmp_dir, container_id, 'student')
            os.mkdir(container_path)
            os.mkdir(sockets_path)
            os.mkdir(student_path)

            # Start the container
            docker_connection.start(container_id,
                                    binds={os.path.abspath(os.path.join(self.task_folder, task.get_course_id(), task.get_id())): {'ro': True, 'bind': '/ro/task'},
                                           os.path.abspath(sockets_path): {'bind': '/sockets'},
                                           os.path.abspath(student_path): {'bind': '/student'}})

            # Send the input data
            container_input = {"input": inputdata, "limits": limits}
            if debug:
                container_input["debug"] = True
            docker_connection.attach_socket(container_id, {'stdin': 1, 'stream': 1}).send(json.dumps(container_input) + "\n")
        except Exception as e:
            print "Cannot start container! {}".format(e)
            return {'result': 'crash', 'text': 'Cannot start container'}

        # Ask the "cgroup" thread to verify the timeout/memory limit
        self._timeout_watcher.add_container_timeout(container_id, limits.get("time", 30))

        # Wait for completion
        error_timeout = False
        try:
            return_value = docker_connection.wait(container_id, limits.get('hard_time', limits.get("time", 30) * 3))
            if return_value == -1:
                raise Exception('Timed out')
        except:
            print "Container timed out!"
            error_timeout = True

        # Verify that everything went well
        error_timeout = self._timeout_watcher.container_had_error(container_id) or error_timeout
        if error_timeout:
            result = {"result": "timeout"}
        else:
            # Get logs back
            try:
                stdout = str(docker_connection.logs(container_id, stdout=True, stderr=False))
                result = json.loads(stdout)
            except:
                print "Cannot get back stdout of container!"
                result = {'result': 'crash', 'text': 'The grader did not return a readable output'}

        # Remove container
        thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))

        # Delete folders
        rmtree(container_path)

        # Return!
        return result

    def _get_agent_backend_service(self):
        handle_job = self.handle_job

        class AgentService(rpyc.Service):

            def exposed_new_job(self, job_id, course_id, task_id, inputdata, debug, callback_status):
                """ Creates, executes and returns the results of a new job """
                return handle_job(job_id, course_id, task_id, inputdata, debug, callback_status)

        return AgentService
