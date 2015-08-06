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
""" Agent, managing docker (abstract agent) """

import json
import logging
import os.path
from shutil import rmtree, copytree
import thread
import threading
import tempfile
import tarfile
import re

import docker
from docker.utils import kwargs_from_env
import rpyc

from inginious.backend.agent._rpyc_unix_server import UnixSocketServer


class SimpleAgent(object):
    """
        A simple agent that can only handle one request at a time. It should not be used directly.
        The field self.image_aliases should be filled by subclasses
    """
    logger = logging.getLogger("agent")

    def __init__(self, task_directory, course_factory, task_factory, tmp_dir="./agent_tmp"):
        from inginious.backend.agent._cgroup_helper import CGroupTimeoutWatcher, CGroupMemoryWatcher

        self.logger.info("Starting agent")
        self.image_aliases = []
        self.tmp_dir = tmp_dir
        self.task_directory = task_directory
        self.course_factory = course_factory
        self.task_factory = task_factory

        # Delete tmp_dir, and recreate-it again
        try:
            rmtree(tmp_dir)
        except:
            pass

        try:
            os.mkdir(tmp_dir)
        except OSError:
            pass

        # Assert that the folders are *really* empty
        self._force_directory_empty(tmp_dir)

        self.logger.debug("Start cgroup helper")
        self._timeout_watcher = CGroupTimeoutWatcher()
        self._memory_watcher = CGroupMemoryWatcher()
        self._timeout_watcher.start()
        self._memory_watcher.start()

        # Init the internal job count, used to name the directories
        self._internal_job_count_lock = threading.Lock()
        self._internal_job_count = 0

    def _force_directory_empty(self, directory):
        """ Call Docker to empty directories that are still owned by old containers """
        docker_connection = docker.Client(**kwargs_from_env())
        response = docker_connection.create_container(
            "centos",
            volumes={'/todel': {}},
            network_disabled=True,
            command="/bin/bash -c 'rm -Rf /todel/*'"
        )
        container_id = response["Id"]
        docker_connection.start(container_id, binds={os.path.abspath(directory): {'ro': False, 'bind': '/todel'}})
        docker_connection.wait(container_id)
        thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))

    def _get_new_internal_job_id(self):
        """ Get a new internal job id """
        self._internal_job_count_lock.acquire()
        internal_job_id = self._internal_job_count
        self._internal_job_count += 1
        self._internal_job_count_lock.release()
        return internal_job_id

    def handle_get_batch_container_metadata(self, container_name, docker_connection=None):
        """
            Returns the arguments needed by a particular batch container and its description
            :returns: a tuple, in the form
                ("container title",
                 "container description in restructuredtext",
                 {"key":
                    {
                     "type:" "file", #or "text",
                     "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                     "name": "name of the field", #not mandatory in file, default "key"
                     "description": "a short description of what this field is used for", #not mandatory, default ""
                     "custom_key1": "custom_value1",
                     ...
                    }
                 }
                )
        """

        try:
            docker_connection = docker_connection or docker.Client(**kwargs_from_env())
            data = docker_connection.inspect_image(container_name)["ContainerConfig"]["Labels"]
        except:
            self.logger.warning("Cannot inspect container %s", container_name)
            return None, None, None

        if not "org.inginious.batch" in data:
            self.logger.warning("Container %s is not a batch container", container_name)
            return None, None, None

        title = data["org.inginious.batch.title"] if "org.inginious.batch.title" in data else container_name
        description = data["org.inginious.batch.description"] if "org.inginious.batch.description" in data else ""

        # Find valids keys
        args = {}
        for label in data:
            match = re.match(r"^org\.inginious\.batch\.args\.([a-zA-Z0-9\-_]+)$", label)
            if match and data[label] in ["file", "text"]:
                args[match.group(1)] = {"type": data[label]}

        # Parse additional metadata for the keys
        for label in data:
            match = re.match(r"^org\.inginious\.batch\.args\.([a-zA-Z0-9\-_]+)\.([a-zA-Z0-9\-_]+)$", label)
            if match and match.group(1) in args:
                if match.group(2) in ["name", "description"]:
                    args[match.group(1)][match.group(2)] = data[label]
                elif match.group(2) == "path":
                    if re.match(r"^[a-zA-Z\-_\./]+$", data[label]) and ".." not in data[label]:
                        args[match.group(1)]["path"] = data[label]
                else:
                    args[match.group(1)][match.group(2)] = data[label]

        # Add all the unknown metadata
        for key in args:
            if "name" not in args[key]:
                args[key]["name"] = key
            if "path" not in args[key]:
                args[key]["path"] = key
            if "description" not in args[key]:
                args[key]["description"] = ""

        return (title, description, args)

    def handle_batch_job(self, job_id, container_name, input_data):
        """ Creates, executes and returns the results of a batch job.
            The return value of a batch job is always a compressed(gz) tar file.
        :param job_id: The distant job id
        :param container_name: The container image to launch
        :param input_data: a dict containing all the keys of get_batch_container_metadata(container_name)[2].
            The values associated are file-like objects for "file" types and  strings for "text" types.
        :return: a dict, containing either:
            - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
                if everything went well. (where file is a tgz file containing the content of the /output folder from the container)
            - {"retval":"...", "stdout": "...", "stderr":"..."}
                if the container crashed (retval is an int != 0) (can also contain file, but not mandatory)
            - {"retval":-1, "stderr": "the error message"}
                if the container failed to start
        """
        self.logger.info("Received request for jobid %s (batch job)", job_id)
        internal_job_id = self._get_new_internal_job_id()
        self.logger.debug("New Internal job id -> %i", internal_job_id)

        # Initialize connection to Docker
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return {'retval': -1, "stderr": "Failed to connect to Docker"}

        batch_args = self.handle_get_batch_container_metadata(container_name, docker_connection)[2]
        if batch_args is None:
            return {'retval': -1, "stderr": "Inspecting the batch container image failed"}

        container_path = os.path.join(self.tmp_dir, str(internal_job_id))  # tmp_dir/id/
        input_path = os.path.join(container_path, 'input')  # tmp_dir/id/input/
        output_path = os.path.join(container_path, 'output')  # tmp_dir/id/output/
        try:
            rmtree(container_path)
        except:
            pass

        os.mkdir(container_path)
        os.mkdir(input_path)
        os.mkdir(output_path)
        os.chmod(container_path, 0777)
        os.chmod(input_path, 0777)
        os.chmod(output_path, 0777)

        try:
            if set(input_data.keys()) != set(batch_args.keys()):
                raise Exception("Invalid keys for inputdata")

            for key in batch_args:
                if batch_args[key]["type"] == "text":
                    if not isinstance(input_data[key], basestring):
                        raise Exception("Invalid value for inputdata: the value for key {} should be a string".format(key))
                    open(os.path.join(input_path, batch_args[key]["path"]), 'w').write(input_data[key])
                elif batch_args[key]["type"] == "file":
                    if isinstance(input_data[key], basestring):
                        raise Exception("Invalid value for inputdata: the value for key {} should be a file object".format(key))
                    open(os.path.join(input_path, batch_args[key]["path"]), 'w').write(input_data[key].read())
        except:
            rmtree(container_path)
            return {'retval': -1, "stderr": 'Invalid tgz for input'}

        # Run the container
        try:
            response = docker_connection.create_container(
                container_name,
                volumes={'/input': {}, '/output': {}}
            )
            container_id = response["Id"]

            # Start the container
            docker_connection.start(container_id,
                                    binds={os.path.abspath(input_path): {'ro': False, 'bind': '/input'},
                                           os.path.abspath(output_path): {'ro': False, 'bind': '/output'}})
        except Exception as e:
            self.logger.warning("Cannot start container! %s", str(e))
            rmtree(container_path)
            return {'retval': -1, "stderr": 'Cannot start container'}

        # Wait for completion
        return_value = -1
        try:
            return_value = docker_connection.wait(container_id)
        except:
            self.logger.info("Container for job id %s crashed", job_id)

        # If docker cannot do anything...
        if return_value == -1:
            rmtree(container_path)
            return {'retval': -1, "stderr": 'Container crashed at startup'}

        # Get logs back
        stdout = ""
        stderr = ""
        try:
            stdout = str(docker_connection.logs(container_id, stdout=True, stderr=False))
            stderr = str(docker_connection.logs(container_id, stdout=True, stderr=False))
        except:
            self.logger.warning("Cannot get back stdout of container %s!", container_id)
            rmtree(container_path)
            return {'retval': -1, "stderr": 'Cannot retrieve stdout/stderr from container'}

        # Tgz the files in /output
        try:
            tmpfile = tempfile.TemporaryFile()
            tar = tarfile.open(fileobj=tmpfile, mode='w:gz')
            tar.add(output_path, '/', True)
            tar.close()
            tmpfile.flush()
            tmpfile.seek(0)
        except:
            rmtree(container_path)
            return {'retval': -1, "stderr": 'The agent was unable to archive the /output directory'}

        return {'retval': return_value, "stdout": stdout, "stderr": stderr, "file": tmpfile}

    def handle_job(self, job_id, course_id, task_id, inputdata, debug, _callback_status):
        """ Creates, executes and returns the results of a new job
        :param job_id: The distant job id
        :param course_id: The course id of the linked task
        :param task_id: The task id of the linked task
        :param inputdata: Input data, given by the student (dict)
        :param debug: A boolean, indicating if the job should be run in debug mode or not
        :param _callback_status: Not used, should be None.
        """
        self.logger.info("Received request for jobid %s", job_id)
        internal_job_id = self._get_new_internal_job_id()
        self.logger.debug("New Internal job id -> %i", internal_job_id)

        # Initialize connection to Docker
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return {'result': 'crash', 'text': 'Cannot connect to Docker'}

        # Get back the task data (for the limits)
        try:
            task = self.course_factory.get_task(course_id, task_id)
        except:
            self.logger.warning("Task %s/%s unavailable on this agent", course_id, task_id)
            return {'result': 'crash', 'text': 'Task unavailable on agent. Please retry later, the agents should synchronize soon. If the error '
                                               'persists, please contact your course administrator.'}

        limits = task.get_limits()

        mem_limit = limits.get("memory", 100)
        if mem_limit < 20:
            mem_limit = 20

        environment = task.get_environment()
        if environment not in self.image_aliases:
            self.logger.warning("Task %s/%s ask for an unknown environment %s (not in aliases)", course_id, task_id, environment)
            return {'result': 'crash', 'text': 'Unknown container. Please contact your course administrator.'}
        environment = self.image_aliases[environment]

        # Remove possibly existing older folder and creates the new ones
        container_path = os.path.join(self.tmp_dir, str(internal_job_id))  # tmp_dir/id/
        task_path = os.path.join(container_path, 'task')  # tmp_dir/id/task/
        sockets_path = os.path.join(container_path, 'sockets')  # tmp_dir/id/socket/
        student_path = os.path.join(task_path, 'student')  # tmp_dir/id/task/student/
        try:
            rmtree(container_path)
        except:
            pass

        os.mkdir(container_path)
        os.mkdir(sockets_path)
        os.chmod(container_path, 0777)
        os.chmod(sockets_path, 0777)

        copytree(os.path.join(self.task_directory, task.get_course_id(), task.get_id()), task_path)
        os.chmod(task_path, 0777)

        if not os.path.exists(student_path):
            os.mkdir(student_path)
            os.chmod(student_path, 0777)

        # Run the container
        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                volumes={'/task': {}, '/sockets': {}},
                network_disabled=True
            )
            container_id = response["Id"]

            # Start the RPyC server associated with this container
            container_set = set()
            student_container_management_service = self._get_agent_student_container_service(
                container_set,
                student_path,
                task.get_environment(),
                limits.get("time", 30),
                mem_limit)

            # Small workaround for error "AF_UNIX path too long" when the agent is launched inside a container. Resolve all symlinks to reduce the
            # path length.
            smaller_path_to_socket = os.path.realpath(os.path.join(sockets_path, 'INGInious.sock'))

            student_container_management = UnixSocketServer(
                student_container_management_service,
                socket_path=smaller_path_to_socket,
                protocol_config={"allow_public_attrs": True, 'allow_pickle': True})

            student_container_management_thread = threading.Thread(target=student_container_management.start)
            student_container_management_thread.daemon = True
            student_container_management_thread.start()

            # Start the container
            docker_connection.start(container_id,
                                    binds={os.path.abspath(task_path): {'ro': False, 'bind': '/task'},
                                           os.path.abspath(sockets_path): {'ro': False, 'bind': '/sockets'}},
                                    mem_limit=mem_limit * 1024 * 1024,
                                    memswap_limit=mem_limit * 1024 * 1024,  # disable swap
                                    oom_kill_disable=True)

            # Send the input data
            container_input = {"input": inputdata, "limits": limits}
            if debug:
                container_input["debug"] = True
            docker_connection.attach_socket(container_id, {'stdin': 1, 'stream': 1}).send(json.dumps(container_input) + "\n")
        except Exception as e:
            self.logger.warning("Cannot start container! %s", str(e))
            rmtree(container_path)
            return {'result': 'crash', 'text': 'Cannot start container'}

        # Ask the "cgroup" thread to verify the timeout/memory limit
        self._timeout_watcher.add_container_timeout(container_id, limits.get("time", 30), limits.get('hard_time', limits.get("time", 30) * 3))
        self._memory_watcher.add_container_memory_limit(container_id, mem_limit)

        # Wait for completion
        error_occured = False
        try:
            return_value = docker_connection.wait(container_id, limits.get('hard_time', limits.get("time", 30) * 4))
            if return_value == -1:
                raise Exception('Container crashed!')
        except:
            self.logger.info("Container for job id %s crashed", job_id)
            error_occured = True

        # Verify that everything went well
        error_timeout = self._timeout_watcher.container_had_error(container_id)
        error_memory = self._memory_watcher.container_had_error(container_id)
        if error_timeout:
            result = {"result": "timeout"}
        elif error_memory:
            result = {"result": "overflow"}
        elif error_occured:
            result = {"result": "crash", "text": "An unknown error occurred while running the container"}
        else:
            # Get logs back
            try:
                stdout = str(docker_connection.logs(container_id, stdout=True, stderr=False))
                result = json.loads(stdout)
            except Exception as e:
                self.logger.warning("Cannot get back stdout of container %s! (%s)", container_id, str(e))
                result = {'result': 'crash', 'text': 'The grader did not return a readable output'}

        # Close RPyC server
        student_container_management.close()

        # Remove container
        thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))

        # Remove subcontainers
        for i in container_set:
            # Also deletes them from the timeout/memory watchers
            self._timeout_watcher.container_had_error(container_id)
            self._memory_watcher.container_had_error(container_id)
            thread.start_new_thread(docker_connection.remove_container, (i, True, False, True))

        # Delete folders
        rmtree(container_path)

        # Return!
        return result

    def _create_new_student_container(self, container_name, working_dir, command, memory_limit, time_limit, hard_time_limit, container_set,
                                      student_path):
        self.logger.debug("Starting new student container... %s %s %s %s %s %s", container_name, working_dir, command, memory_limit, time_limit,
                          hard_time_limit)
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return None, None, "Cannot connect to Docker!"

        mem_limit = memory_limit or 100
        if mem_limit < 20:
            mem_limit = 20

        if container_name not in self.image_aliases:
            self.logger.info("Unknown environment %s (not in aliases)", container_name)
            return None, None, "Unknown environment {} (not in aliases)".format(container_name)
        environment = self.image_aliases[container_name]

        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                network_disabled=True,
                volumes={'/task/student': {}},
                command=command,
                working_dir=working_dir,
                user="4242"
            )
            container_id = response["Id"]

            # Start the container
            docker_connection.start(container_id,
                                    binds={os.path.abspath(student_path): {'ro': False, 'bind': '/task/student'}},
                                    mem_limit=mem_limit * 1024 * 1024,  # add 10 mo of bonus, as we check the memory in the "cgroup" thread
                                    memswap_limit=mem_limit * 1024 * 1024,  # disable swap
                                    oom_kill_disable=True
                                    )

            stdout_err = docker_connection.attach_socket(container_id, {'stdin': 0, 'stdout': 1, 'stderr': 1, 'stream': 1, 'logs': 1})
        except Exception as e:
            self.logger.warning("Cannot start container! %s", e)
            return None, None, "Cannot start container! {}".format(e)

        container_set.add(container_id)
        # Ask the "cgroup" thread to verify the timeout/memory limit
        self._timeout_watcher.add_container_timeout(container_id, time_limit, min(time_limit * 4, hard_time_limit))
        self._memory_watcher.add_container_memory_limit(container_id, mem_limit)

        self.logger.info("New student container started")
        return container_id, stdout_err, None

    def _student_container_signal(self, container_id, signalnum):
        self.logger.info("Sending signal %s to student container", str(signalnum))
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return False

        docker_connection.kill(container_id, signalnum)
        return True

    def _student_container_get_stdin(self, container_id):
        self.logger.info("Getting stdin of student container")
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return None

        stdin = docker_connection.attach_socket(container_id, {'stdin': 1, 'stderr': 0, 'stdout': 0, 'stream': 1})
        self.logger.info("Returning stdin of student container")
        return stdin

    def _student_container_close(self, container_id, container_set):
        self.logger.info("Closing student container")

        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return 254

        # Wait for completion
        return_value = 254
        try:
            return_value = docker_connection.wait(container_id)
            if return_value == -1:
                return_value = 254
                raise Exception('Container crashed!')
        except:
            pass

        # Verify that everything went well
        if self._timeout_watcher.container_had_error(container_id):
            return_value = 253
        if self._memory_watcher.container_had_error(container_id):
            return_value = 252

        # Remove container
        thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))
        container_set.remove(container_id)

        # Return!
        return return_value

    def _get_agent_student_container_service(self, container_set, student_path, default_container, default_time, default_memory):
        create_new_student_container = self._create_new_student_container
        student_container_signal = self._student_container_signal
        student_container_get_stdin = self._student_container_get_stdin
        student_container_close = self._student_container_close

        class StudentContainerManagementService(rpyc.Service):

            def exposed_run(self, container_name, working_dir, command, memory_limit, time_limit, hard_time_limit):
                if container_name == "":
                    container_name = default_container
                if memory_limit == 0:
                    memory_limit = default_memory
                if time_limit == 0:
                    time_limit = default_time
                if hard_time_limit == 0:
                    hard_time_limit = 3 * time_limit
                return create_new_student_container(str(container_name), str(working_dir), str(command), int(memory_limit), int(time_limit),
                                                    int(hard_time_limit), container_set, student_path)

            def exposed_signal(self, container_id, signalnum):
                if container_id in container_set:
                    return student_container_signal(str(container_id), int(signalnum))
                return None

            def exposed_stdin(self, container_id):
                if container_id in container_set:
                    return student_container_get_stdin(str(container_id))
                return None

            def exposed_close(self, container_id):
                if container_id in container_set:
                    return student_container_close(str(container_id), container_set)
                return None

        return StudentContainerManagementService
