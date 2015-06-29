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

import docker
from docker.utils import kwargs_from_env
import rpyc

from backend_agent._rpyc_unix_server import UnixSocketServer
import common.base
from common.courses import Course


class SimpleAgent(object):
    """
        A simple agent that can only handle one request at a time. It should not be used directly.
        The field self.image_aliases should be filled by subclasses
    """
    logger = logging.getLogger("agent")

    def __init__(self, tmp_dir="./agent_tmp"):
        from backend_agent._cgroup_helper import CGroupTimeoutWatcher, CGroupMemoryWatcher

        self.logger.info("Starting agent")
        self.image_aliases = []
        self.tmp_dir = tmp_dir

        try:
            os.mkdir(tmp_dir)
        except OSError:
            pass

        self.logger.debug("Start cgroup helper")
        self._timeout_watcher = CGroupTimeoutWatcher()
        self._memory_watcher = CGroupMemoryWatcher()
        self._timeout_watcher.start()
        self._memory_watcher.start()

        # Init the internal job count, used to name the directories
        self._internal_job_count_lock = threading.Lock()
        self._internal_job_count = 0

    def handle_job(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        """ Creates, executes and returns the results of a new job
        :param job_id: The distant job id
        :param course_id: The course id of the linked task
        :param task_id: The task id of the linked task
        :param inputdata: Input data, given by the student (dict)
        :param debug: A boolean, indicating if the job should be run in debug mode or not
        :param callback_status: Not used, should be None.
        """
        self.logger.info("Received request for jobid %s", job_id)

        # Get the internal job count
        self._internal_job_count_lock.acquire()
        internal_job_id = self._internal_job_count
        self._internal_job_count += 1
        self._internal_job_count_lock.release()
        self.logger.debug("New Internal job id -> %i", internal_job_id)

        # Initialize connection to Docker
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return {'result': 'crash', 'text': 'Cannot connect to Docker'}

        # Get back the task data (for the limits)
        try:
            task = Course(course_id).get_task(task_id)
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

        copytree(os.path.join(common.base.get_tasks_directory(), task.get_course_id(), task.get_id()), task_path)
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
                                    oom_kill_disable=True
                                    )

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
                print e
                self.logger.warning("Cannot get back stdout of container %s!", container_id)
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
                working_dir=working_dir
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
