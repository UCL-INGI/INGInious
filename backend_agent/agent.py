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
import threading
import traceback

import docker
from docker.utils import kwargs_from_env
import rpyc
from rpyc.utils.server import ThreadedServer

from backend_agent.cgroup_helper import CGroupTimeoutWatcher, CGroupMemoryWatcher
from backend_agent.rpyc_unix_server import UnixSocketServer
import common.base
from common.courses import Course


class Agent(object):

    def __init__(self, master_port, image_aliases, task_folder="./tasks", tmp_dir="./agent_tmp", cgroup_location="/sys/fs/cgroups"):
        logging.info("Starting agent")
        self.image_aliases = image_aliases
        common.base.init_common_lib(task_folder, [], 1)  # we do not need to upload file, so not needed here
        self.task_folder = task_folder
        self.cgroup_location = cgroup_location
        self.tmp_dir = tmp_dir

        try:
            os.mkdir(tmp_dir)
        except:
            pass

        print "Start cgroup helper"
        self._timeout_watcher = CGroupTimeoutWatcher()
        self._memory_watcher = CGroupMemoryWatcher()
        self._timeout_watcher.start()
        self._memory_watcher.start()

        # Init the internal job count, used to name the directories
        self._internal_job_count_lock = threading.Lock()
        self._internal_job_count = 0

        print "Starting RPyC server - backend connection"
        self._backend_server = ThreadedServer(self._get_agent_backend_service(), port=master_port, protocol_config={"allow_public_attrs": True, 'allow_pickle': True})
        self._backend_server.start()

    def handle_job(self, job_id, course_id, task_id, inputdata, debug, _):
        print "Received request for jobid {}".format(job_id)

        # Deepcopy inputdata (to bypass "passage by reference" of RPyC)
        inputdata = copy.deepcopy(inputdata)

        # Get the internal job count
        self._internal_job_count_lock.acquire()
        internal_job_id = self._internal_job_count
        self._internal_job_count += 1
        self._internal_job_count_lock.release()
        print "Internal job count -> {}".format(internal_job_id)

        # Initialize connection to Docker
        try:
            docker_connection = docker.Client(**kwargs_from_env())
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

        # Remove possibly existing older folder and creates the new ones
        container_path = os.path.join(self.tmp_dir, str(internal_job_id))
        sockets_path = os.path.join(self.tmp_dir, str(internal_job_id), 'sockets')
        student_path = os.path.join(self.tmp_dir, str(internal_job_id), 'student')
        try:
            rmtree(container_path)
        except:
            pass

        os.mkdir(container_path)
        os.mkdir(sockets_path)
        os.mkdir(student_path)

        # Run the container
        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                volumes={'/ro/task': {}, '/sockets': {}, '/student': {}},
                mem_limit=(mem_limit + 10) * 1024 * 1024  # add 10 mo of bonus, as we check the memory in the "cgroup" thread
            )
            container_id = response["Id"]

            # Start the RPyC server associated with this container
            container_set = set()
            student_container_management_service = self._get_agent_student_container_service(
                container_set,
                sockets_path,
                task.get_environment(),
                limits.get("time", 30),
                mem_limit)
            student_container_management = UnixSocketServer(
                student_container_management_service,
                socket_path=os.path.join(sockets_path, 'INGInious.sock'),
                protocol_config={"allow_public_attrs": True, 'allow_pickle': True})
            student_container_management_thread = threading.Thread(target=student_container_management.start)
            student_container_management_thread.daemon = True
            student_container_management_thread.start()

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
            traceback.print_exc()
            print "Cannot start container! {}".format(e)
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
            print "Container crashed!"
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
            except:
                print "Cannot get back stdout of container!"
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

    def _get_agent_backend_service(self):
        """ Returns a RPyC service associated with this Agent """
        handle_job = self.handle_job

        class AgentService(rpyc.Service):

            def exposed_new_job(self, job_id, course_id, task_id, inputdata, debug, callback_status):
                """ Creates, executes and returns the results of a new job """
                return handle_job(job_id, course_id, task_id, inputdata, debug, callback_status)

        return AgentService

    def _create_new_student_container(self, container_name, command, memory_limit, time_limit, hard_time_limit, container_set, student_path):
        print "Starting new student container... {} {} {} {} {}".format(container_name, command, memory_limit, time_limit, hard_time_limit)
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            print "Cannot connect to Docker!"
            return None, None, "Cannot connect to Docker!"

        mem_limit = memory_limit or 100
        if mem_limit < 20:
            mem_limit = 20

        if container_name not in self.image_aliases:
            print "Unknown environment {} (not in aliases)".format(container_name)
            return None, None, "Unknown environment {} (not in aliases)".format(container_name)
        environment = self.image_aliases[container_name]

        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                network_disabled=True,
                volumes={'/student': {}},
                command=command,
                mem_limit=(mem_limit + 10) * 1024 * 1024  # add 10 mo of bonus, as we check the memory in the "cgroup" thread
            )
            container_id = response["Id"]

            # Start the container
            docker_connection.start(container_id, binds={os.path.abspath(student_path): {'bind': '/student'}})

            stdout_err = docker_connection.attach_socket(container_id, {'stdin': 0, 'stdout': 1, 'stderr': 1, 'stream': 1, 'logs': 1})
        except Exception as e:
            traceback.print_exc()
            print "Cannot start container! {}".format(e)
            return None, None, "Cannot start container! {}".format(e)

        container_set.add(container_id)
        # Ask the "cgroup" thread to verify the timeout/memory limit
        self._timeout_watcher.add_container_timeout(container_id, time_limit, min(time_limit * 4, hard_time_limit))
        self._memory_watcher.add_container_memory_limit(container_id, mem_limit)

        print "New student container started"
        return container_id, stdout_err, None

    def _student_container_signal(self, container_id, signalnum):
        print "Sending signal {} to student container".format(str(signalnum))
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            print "Cannot connect to Docker!"
            return False

        docker_connection.kill(container_id, signalnum)
        return True

    def _student_container_get_stdin(self, container_id):
        print "Getting stdin of student container"
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            print "Cannot connect to Docker!"
            return None

        stdin = docker_connection.attach_socket(container_id, {'stdin': 1, 'stderr': 0, 'stdout': 0, 'stream': 1})
        print "Returning stdin of student container"
        return stdin

    def _student_container_close(self, container_id, container_set):
        print "Closing student container"

        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            print "Cannot connect to Docker!"
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

            def exposed_run(self, container_name, command, memory_limit, time_limit, hard_time_limit):
                if container_name == "":
                    container_name = default_container
                if memory_limit == 0:
                    memory_limit = default_memory
                if time_limit == 0:
                    time_limit = default_time
                if hard_time_limit == 0:
                    hard_time_limit = 3 * time_limit
                return create_new_student_container(str(container_name), str(command), int(memory_limit), int(time_limit), int(hard_time_limit), container_set, student_path)

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
