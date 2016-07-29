# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Agent, managing docker (abstract agent) """

import json
import logging
import os.path
from shutil import rmtree, copytree
import _thread
import threading
import tempfile
import tarfile
import re
import time
import asyncio

import docker
from docker.utils import kwargs_from_env, create_host_config

from inginious.backend.agent.remote_ssh_manager import RemoteSSHManager


class SimpleAgent(object):
    """
        A simple agent that can only handle one request at a time. It should not be used directly.
        The field self.image_aliases should be filled by subclasses
    """
    logger = logging.getLogger("agent")

    def __init__(self, task_directory, course_factory, task_factory, ssh_manager_location, tmp_dir="./agent_tmp"):
        """
        :param task_directory:
        :param course_factory:
        :param task_factory:
        :param ssh_manager_location: port or filename(unix socket) to bind to. If None, remote debugging is deactivated
        :param tmp_dir:
        :return:
        """
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

        if ssh_manager_location is not None:
            self.remote_ssh_manager = RemoteSSHManager(ssh_manager_location)
        else:
            self.remote_ssh_manager = None

        self.logger.debug("Start cgroup helper")
        self._timeout_watcher = CGroupTimeoutWatcher()
        self._memory_watcher = CGroupMemoryWatcher()
        self._timeout_watcher.start()
        self._memory_watcher.start()

        # Init the internal job count, used to name the directories
        self._internal_job_count_lock = threading.Lock()
        self._internal_job_count = 0

        # Dict that stores running container ids for each job id
        self._container_for_job = {}

        # Stores container id of killed containers
        self._killed_containers = set()

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
        _thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))

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
        os.chmod(container_path, 0o777)
        os.chmod(input_path, 0o777)
        os.chmod(output_path, 0o777)

        try:
            if set(input_data.keys()) != set(batch_args.keys()):
                raise Exception("Invalid keys for inputdata")

            for key in batch_args:
                if batch_args[key]["type"] == "text":
                    if not isinstance(input_data[key], str):
                        raise Exception("Invalid value for inputdata: the value for key {} should be a string".format(key))
                    open(os.path.join(input_path, batch_args[key]["path"]), 'w').write(input_data[key])
                elif batch_args[key]["type"] == "file":
                    if isinstance(input_data[key], str):
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
        return_value = self._wait_for_container_completion(docker_connection, container_id, None)

        # If docker cannot do anything...
        if return_value == -1:
            self.logger.info("Container for job id %s crashed", job_id)
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

    def handle_job(self, job_id, course_id, task_id, inputdata, debug, ssh_callback):
        """ Creates, executes and returns the results of a new job
        :param job_id: The distant job id
        :param course_id: The course id of the linked task
        :param task_id: The task id of the linked task
        :param inputdata: Input data, given by the student (dict)
        :param debug: Can be False (normal mode), True (outputs more data), or "ssh" (starts an ssh server in the container)
        :param ssh_callback: ssh callback function. Takes two parameters: (conn_id, private_key). Is only called if debug == "ssh".
        """
        self.logger.info("Received request for jobid %s", job_id)
        internal_job_id = self._get_new_internal_job_id()
        self.logger.debug("New Internal job id -> %i", internal_job_id)

        # Verify some arguments
        if debug == "ssh" and ssh_callback is None:
            return {'result': 'crash', 'text': 'Agent error message: debug mode is set as ssh, but ssh_callback is None.'}
        if debug == "ssh" and self.remote_ssh_manager is None:
            return {'result': 'crash', 'text': 'Remote debugging is not activated on this agent.'}

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
            self.logger.warning("Task %s/%s unavailable on this agent", course_id, task_id, exc_info=True)
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
        os.chmod(container_path, 0o777)
        os.chmod(sockets_path, 0o777)

        copytree(os.path.join(self.task_directory, task.get_course_id(), task.get_id()), task_path)
        os.chmod(task_path, 0o777)

        if not os.path.exists(student_path):
            os.mkdir(student_path)
            os.chmod(student_path, 0o777)

        # Run the container
        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                volumes={'/task': {}, '/sockets': {}},
                network_disabled=not (task.allow_network_access_grading() or debug == "ssh"),
                host_config = docker_connection.create_host_config(
                    mem_limit=str(mem_limit) + "M",
                    memswap_limit=str(mem_limit) + "M",
                    mem_swappiness=0,
                    oom_kill_disable=True,
                        network_mode=("bridge" if (task.allow_network_access_grading() or debug == "ssh") else 'none'),
                        binds={os.path.abspath(task_path): {'ro': False, 'bind': '/task'},
                               os.path.abspath(sockets_path): {'ro': False, 'bind': '/sockets'}}
                )
            )
            container_id = response["Id"]
            self._container_for_job[job_id] = container_id

            # Start a socket to communicate between the agent and the container
            container_set = set()
            student_container_management_server_fact = lambda: self._get_agent_student_container_server(
                container_id,
                container_set,
                student_path,
                task.get_environment(),
                limits.get("time", 30),
                mem_limit)

            # Small workaround for error "AF_UNIX path too long" when the agent is launched inside a container. Resolve all symlinks to reduce the
            # path length.
            smaller_path_to_socket = os.path.realpath(os.path.join(sockets_path, 'INGInious.sock'))

            event_loop = asyncio.get_event_loop()
            def start_server():
                server = event_loop.create_unix_server(student_container_management_server_fact, smaller_path_to_socket)
                event_loop.create_task(server)
            event_loop.call_soon_threadsafe(start_server)

            # Start the container
            docker_connection.start(container_id)

            # Send the input data
            container_input = {"input": inputdata, "limits": limits}
            if debug:
                container_input["debug"] = debug
            self.logger.debug("%s", json.dumps(container_input))
            docker_connection.attach_socket(container_id, {'stdin': 1, 'stream': 1}).send(json.dumps(container_input) + "\n")
        except Exception as e:
            self.logger.warning("Cannot start container! %s", str(e))
            rmtree(container_path)

            try:
                del self._container_for_job[job_id]
            except:
                pass

            return {'result': 'crash', 'text': 'Cannot start container'}

        # Ask the "cgroup" thread to verify the timeout/memory limit
        time_limit = limits.get("time", 30)
        hard_time_limit = limits.get('hard_time', time_limit * 3)
        if debug == "ssh":  # allow 30 minutes of real time.
            time_limit = 30 * 60
            hard_time_limit = 30 * 60
        self._timeout_watcher.add_container_timeout(container_id, time_limit, hard_time_limit)
        self._memory_watcher.add_container_memory_limit(container_id, mem_limit)

        # If ssh mode is activated, get the ssh key
        if debug == "ssh":
            self._handle_container_ssh_start(docker_connection, container_id, job_id, ssh_callback)

        # Wait for completion
        error_occured = False
        if self._wait_for_container_completion(docker_connection, container_id, int(hard_time_limit * 1.2)) == -1:
            self.logger.info("Container for job id %s crashed", job_id)
            error_occured = True

        if debug == "ssh":
            self._handle_container_ssh_close(job_id)

        del self._container_for_job[job_id]

        # Verify that everything went well
        error_killed = self._container_was_killed(container_id)
        error_timeout = self._timeout_watcher.container_had_error(container_id)
        error_memory = self._memory_watcher.container_had_error(container_id)
        if error_killed:
            result = {"result": "killed"}
        elif error_timeout:
            result = {"result": "timeout"}
        elif error_memory:
            result = {"result": "overflow"}
        elif error_occured:
            result = {"result": "crash", "text": "An unknown error occurred while running the container"}
        else:
            # Get logs back
            try:
                stdout = str(docker_connection.logs(container_id, stdout=True, stderr=False))
                self.logger.debug(stdout)
                if debug == "ssh":  # skip the first line of the output, that contained the ssh key
                    stdout = "\n".join(stdout.split("\n")[1:])
                self.logger.debug(stdout)
                result = json.loads(stdout)
            except Exception as e:
                self.logger.warning("Cannot get back stdout of container %s! (%s)", container_id, str(e))
                result = {'result': 'crash', 'text': 'The grader did not return a readable output'}

        # Close RPyC server
        student_container_management.close()

        # Remove container
        _thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))

        # Remove subcontainers
        for i in container_set:
            # Also deletes them from the timeout/memory watchers
            self._timeout_watcher.container_had_error(container_id)
            self._memory_watcher.container_had_error(container_id)
            _thread.start_new_thread(docker_connection.remove_container, (i, True, False, True))

        # Delete folders
        rmtree(container_path)

        # Return!
        return result

    def _create_new_student_container(self, container_name, working_dir, command, memory_limit, time_limit, hard_time_limit, share_network,
                                      parent_container_id, container_set, student_path):
        self.logger.debug("Starting new student container... %s %s %s %s %s %s", container_name, working_dir, command, memory_limit, time_limit,
                          hard_time_limit)
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return None, "Cannot connect to Docker!"

        mem_limit = memory_limit or 100
        if mem_limit < 20:
            mem_limit = 20

        if container_name not in self.image_aliases:
            self.logger.info("Unknown environment %s (not in aliases)", container_name)
            return None, "Unknown environment {} (not in aliases)".format(container_name)
        environment = self.image_aliases[container_name]

        try:
            response = docker_connection.create_container(
                environment,
                stdin_open=True,
                network_disabled=(not share_network),
                volumes={'/task/student': {}},
                command=command,
                working_dir=working_dir,
                user="4242",
                host_config=docker_connection.create_host_config(
                    mem_limit=str(mem_limit) + "M",
                    memswap_limit= str(mem_limit) + "M",
                    mem_swappiness=0,
                    oom_kill_disable=True,
                    network_mode=('none' if not share_network else ('container:' + parent_container_id)),
                    binds={os.path.abspath(student_path): {'ro': False, 'bind': '/task/student'}}
                )
            )
            container_id = response["Id"]

            # Start the container
            docker_connection.start(container_id)
        except Exception as e:
            self.logger.warning("Cannot start container! %s", e)
            return None, "Cannot start container! {}".format(e)

        container_set.add(container_id)
        # Ask the "cgroup" thread to verify the timeout/memory limit
        self._timeout_watcher.add_container_timeout(container_id, time_limit, min(time_limit * 4, hard_time_limit))
        self._memory_watcher.add_container_memory_limit(container_id, mem_limit)

        self.logger.info("New student container started")
        return container_id, None

    def _student_container_signal(self, container_id, signalnum):
        self.logger.info("Sending signal %s to student container", str(signalnum))
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return False

        docker_connection.kill(container_id, signalnum)
        return True

    def _student_container_get_stdX(self, container_id, stdin=True, stdout=False, stderr=False):
        self.logger.info("Getting stdX of student container")
        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return None

        socket = docker_connection.attach_socket(container_id, {'stdin' : (1 if stdin  else 0),
                                                                'stderr': (1 if stderr else 0),
                                                                'stdout': (1 if stdout else 0),
                                                                'stream': 1})
        self.logger.info("Returning stdX of student container")
        return socket

    def _student_container_close(self, container_id, container_set):
        self.logger.info("Closing student container")

        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.warning("Cannot connect to Docker!")
            return 254

        # Wait for completion
        return_value = self._wait_for_container_completion(docker_connection, container_id, None)
        if return_value == -1:
            return_value = 254

        # Verify that everything went well
        if self._timeout_watcher.container_had_error(container_id):
            return_value = 253
        if self._memory_watcher.container_had_error(container_id):
            return_value = 252

        # Remove container
        _thread.start_new_thread(docker_connection.remove_container, (container_id, True, False, True))
        container_set.remove(container_id)

        # Return!
        return return_value

    def _get_agent_student_container_server(self, parent_container_id, container_set, student_path, default_container, default_time, default_memory):
        return DockerTransfertProtocolServer(asyncio.get_event_loop(), parent_container_id, container_set, student_path, default_container,
                                             default_time, default_memory, self._create_new_student_container, self._student_container_get_stdX,
                                             self._student_container_signal, self._student_container_close)

    def _wait_for_container_completion(self, docker_connection, container_id, max_time):
        """ Wait for container completion. Returns the return value of the command or -1 if an error happened. """
        try:
            return_value = docker_connection.wait(container_id, max_time)
        except:
            return_value = -1
        self.logger.debug("Container id %s ended with %i", container_id, return_value)
        return return_value

    def _handle_container_ssh_start(self, docker_connection, container_id, job_id, ssh_callback):
        """ Handle the creation of the distant SSH server """
        if self.remote_ssh_manager is None:
            raise Exception("Remote debugging is not activated")

        ssh_key = None
        for attempt in range(0, 30):
            try:
                stdout = str(docker_connection.logs(container_id, stdout=True, stderr=False))
                stdout = stdout.split("\n")[0]
                stdout = json.loads(stdout)
                ssh_key = stdout["ssh_key"]
                self.logger.debug('Got SSH key for job %s', job_id)
                break
            except Exception as e:
                self.logger.debug("Cannot get SSH for job %s: %s. Retrying...", job_id, str(e))
            time.sleep(1)

        if ssh_key is None:
            return

        try:
            ip = docker_connection.inspect_container(container_id)["NetworkSettings"]["IPAddress"]
        except:
            self.logger.debug("Cannot inspect container to find IP, for job %s", job_id)
            return

        self.logger.debug("Got IP for SSH connection of job id %s: %s", job_id, ip)
        self.remote_ssh_manager.add_open_connection(job_id, ip, 22)
        self.logger.debug("Start key for the inginious-remote-debug command:\n%s\n%s", job_id, ssh_key)

        if ssh_callback is not None:
            try:
                ssh_callback(job_id, ssh_key)
            except:
                self.logger.warning("Cannot call ssh_callback for job id %s", job_id)

    def _handle_container_ssh_close(self, job_id):
        """ Marks as closed a distant SSH server """
        if self.remote_ssh_manager is None:
            raise Exception("Remote debugging is not activated")

        self.remote_ssh_manager.del_connection(job_id)

    def _container_was_killed(self, container_id):
        """ Returns True (/False) if the container was (/not) killed by the remote job manager. Can only be called ONCE for each container_id """
        if container_id in self._killed_containers:
            self._killed_containers.remove(container_id)
            return True
        return False

    def kill_job(self, job_id):
        """ Kill a running job """
        container_id = self._container_for_job.get(job_id)
        if container_id is None:
            self.logger.error("Invalid job_id submitted to kill_job")
            return False

        # Add it now, even if the container is not really killed.
        self._killed_containers.add(container_id)

        try:
            docker_connection = docker.Client(**kwargs_from_env())
        except:
            self.logger.error("kill_job cannot connect to Docker!")
            return False

        try:
            docker_connection.kill(container_id)
            return True
        except Exception as e:
            self.logger.info("Cannot kill container %s: %s", container_id, str(e))
            return False


class DockerTransfertProtocolClient(asyncio.Protocol):
    def __init__(self, out):
        self.out = out

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):

        # Check that the main transport has not closed yet
        if self.out.is_closing():
            self.transport.close()
            return

        self.out.write(data)


class DockerTransfertProtocolClientIn(asyncio.Protocol):
    def __init__(self, set_transport):
        self.set_transport = set_transport

    def connection_made(self, transport):
        self.set_transport(transport)


class DockerTransfertProtocolServer(asyncio.Protocol):
    def __init__(self, event_loop, docker_client, parent_container_id, container_set, student_path, default_container, default_time, default_memory,
                 create_new_student_container, student_container_get_stdX, student_container_signal, student_container_close):
        self._event_loop = event_loop
        self._docker_client = docker_client
        self._parent_container_id = parent_container_id
        self._container_set = container_set
        self._student_path = student_path
        self._default_container = default_container
        self._default_time = default_time
        self._default_memory = default_memory
        self._create_new_student_container = create_new_student_container
        self._student_container_get_stdX = student_container_get_stdX
        self._student_container_signal = student_container_signal
        self._student_container_close = student_container_close

    def connection_made(self, transport):
        """
        Called when a connection is made.
        The argument is the transport representing the pipe connection.
        To receive data, wait for data_received() calls.
        When the connection is closed, connection_lost() is called.
        """
        self.transport = transport
        self.mode = 0  # waiting for instructions
        self.stdin_conn = None
        self.stdin_transport = None
        self.buffer = b""

    def data_received(self, data):
        """
        Called when some data is received.
        The argument is a bytes object.
        """
        if self.mode == 0:    # waiting for instructions
            self.buffer += data
            if "\r\n" in self.buffer:
                commands = self.buffer.split(b"\r\n")
                toparse = commands[0]
                self.buffer = b""
                self._dispatch(toparse)
                if len(commands) > 1:
                    self.data_received(b"\r\n".join(commands[1:])) #repeat to be sure we empty the buffer if needed
        elif self.mode == 1:  # redirect
            self._handle_stdin_redirect(data)
        elif self.mode == 2:  # done
            pass

    def _dispatch(self, data):
        try:
            if data.startwith(b"run"):
                self._handle_run(data)
            elif data.startwith(b"stdout") or data.startwith(b"stderr"):
                self._handle_stdX(data)
            elif data.startwith(b"stdin"):
                self._handle_stdin(data)
            elif data.startwith(b"signal"):
                self._handle_signal(data)
            elif data.startwith(b"close"):
                self._handle_close(data)
            else:
                raise Exception("Unknown command")
        except Exception as e:
            self.transport.write(b"error|"+str(e).encode("utf8")+"\r\n")
            self.transport.close()

    def _handle_signal(self, data):
        data = data.split(b"|")
        self._ensure_containerid(data[1])
        self.transport.write(b"ok|"+str(int(self._student_container_signal(data[1], int(data[2])))).encode("utf8")+b"\r\n")
        self.mode = 2  # done

    def _handle_close(self, data):
        data = data.split(b"|")
        self._ensure_containerid(data[1])
        self.transport.write(b"ok|" + str(int(self._student_container_close(data[1]))).encode("utf8") + b"\r\n")
        self.mode = 2  # done

    def _handle_stdin(self, data):
        data = data.split(b"|")
        self._ensure_containerid(data[1])
        socket = self._student_container_get_stdX(data[1], stdin=True, stdout=False, stderr=False)
        self.std_conn = self._event_loop.create_connection(lambda: DockerTransfertProtocolClientIn(self._set_stdin_transport),
                                                           sock=socket)

        self._event_loop.create_task(self.std_conn)
        self.mode = 1  # stdin

    def _handle_stdX(self, data):
        data = data.split(b"|")
        stdout = False
        stderr = False
        if data[0] == b"stdout":
            stdout = True
        elif data[1] == b"stderr":
            stderr = True
        else:
            raise Exception("unknown operation")
        self._ensure_containerid(data[1])
        socket = self._student_container_get_stdX(data[1], stdin=False, stdout=stdout, stderr=stderr)
        conn = self._event_loop.create_connection(lambda: DockerTransfertProtocolClient(self.transport), sock=socket)
        self._event_loop.create_task(conn)
        self.mode = 2  # stdout/stderr

    def _handle_stdin_redirect(self, data):
        self.stdin_transport.write(data)  # transmit data

    def _handle_run(self, data):
        _, container_name, working_dir, command, memory_limit, time_limit, hard_time_limit, share_network = data.decode("utf8").split("|")
        if container_name == "":
            container_name = self._default_container
        if memory_limit == 0:
            memory_limit = self._default_memory
        if time_limit == 0:
            time_limit = self._default_time
        if hard_time_limit == 0:
            hard_time_limit = 3 * time_limit
        container_id, error = self._create_new_student_container(str(container_name), str(working_dir), str(command), int(memory_limit),
                                                                 int(time_limit), int(hard_time_limit), bool(share_network),
                                                                 self._parent_container_id, self._parent_container_id,
                                                                 self._parent_container_id)
        if error is not None:
            self.transport.write(b"error|" + error.encore("utf8") + b"\r\n")
        else:
            self.transport.write(b"ok|" + str(container_id).encode("utf8") + b"\r\n")

    def _ensure_containerid(self, container_id):
        if container_id not in self._container_set:
            raise Exception("Invalid container id")

    def _set_stdin_transport(self, t):
        self.stdin_transport = t
        self.transport.resume_reading()