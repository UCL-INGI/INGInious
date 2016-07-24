# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import asyncio
import json
import logging
import os
from shutil import rmtree, copytree
from typing import Dict, Any

import zmq
from zmq.asyncio import Poller

from inginious.backend4._asyncio_utils import AsyncIteratorWrapper
from inginious.agent4._cgroup_abstraction import MemoryWatcher, TimeoutWatcher
from inginious.agent4._docker_interface import DockerInterface
from inginious.agent4._pipeline import PipelinePush, PipelinePull
from inginious.backend4.message_meta import ZMQUtils
from inginious.backend4.messages import BackendNewJob, AgentJobStarted, BackendNewBatchJob, BackendKillJob, AgentHello, BackendJobId, AgentJobDone, \
    KWPRegisterContainer, KWPKilledStatus, SPResult, EventContainerDied


class DockerAgent(object):
    def __init__(self, context, backend_addr, nb_sub_agents, task_directory, ssh_manager_location,
                 tmp_dir="./agent_tmp"):
        """
        :param context: ZeroMQ context for this process
        :param backend_addr: address of the backend (for example, "tcp://127.0.0.1:2222")
        :param nb_sub_agents: nb of slots available for this agent
        :param task_directory: path to the task directory
        :param ssh_manager_location: port or filename(unix socket) to bind to. If None, remote debugging is deactivated
        :param tmp_dir: temp dir that is used by the agent to start new containers
        """
        self._logger = logging.getLogger("inginious.agent.docker")

        self._logger.info("Starting agent")

        self._backend_addr = backend_addr
        self._context = context
        self._loop = asyncio.get_event_loop()
        self._nb_sub_agents = nb_sub_agents
        self._containers_running = {}
        self._containers_ending = {}
        self._container_for_job = {}

        self.tmp_dir = tmp_dir
        self.task_directory = task_directory

        self._internal_job_count = 0

        # Delete tmp_dir, and recreate-it again
        try:
            rmtree(tmp_dir)
        except:
            pass

        try:
            os.mkdir(tmp_dir)
        except OSError:
            pass

        # TODO centos img?
        # Assert that the folders are *really* empty
        #self._force_directory_empty(tmp_dir)
        # TODO ssh debug
        #if ssh_manager_location is not None:
        #    self.remote_ssh_manager = RemoteSSHManager(ssh_manager_location)
        #else:
        #    self.remote_ssh_manager = None

        # Docker
        self._docker = DockerInterface()

        # Auto discover containers
        self._logger.info("Discovering containers")
        self._containers = self._docker.get_containers()
        self._batch_containers = self._docker.get_batch_containers()

        # Sockets
        self._backend_socket = self._context.socket(zmq.DEALER)
        self._docker_events_pub = self._context.socket(zmq.PUB)
        self._docker_events_sub = self._context.socket(zmq.SUB)

        # Watchers
        self._killer_watcher_push = PipelinePush(context, "agentpush")
        self._killer_watcher_pull = PipelinePull(context, "agentpull")
        self._timeout_watcher = TimeoutWatcher(context)
        self._memory_watcher = MemoryWatcher(context)

        self._containers_killed = set()

        # Poller
        self._poller = Poller()
        self._poller.register(self._backend_socket, zmq.POLLIN)
        self._poller.register(self._docker_events_sub, zmq.POLLIN)
        self._poller.register(self._killer_watcher_pull.get_pull_socket(), zmq.POLLIN)

        self._docker_interface = DockerInterface()

    async def init_watch_docker_events(self):
        url = "inproc://docker_events"
        self._docker_events_pub.bind(url)
        self._docker_events_sub.connect(url)
        self._docker_events_sub.setsockopt(zmq.SUBSCRIBE, b'')
        self._loop.create_task(self._watch_docker_events())

    async def init_watcher_pipe(self):
        self._loop.create_task(self._timeout_watcher.run_pipeline())
        self._loop.create_task(self._memory_watcher.run_pipeline())
        self._timeout_watcher.link(self._killer_watcher_push)
        self._memory_watcher.link(self._timeout_watcher)
        self._killer_watcher_pull.link(self._memory_watcher)

    async def _watch_docker_events(self):
        source = AsyncIteratorWrapper(self._docker_interface.event_stream(filters={"event":"die"}))
        async for i in source:
            container_id = i["id"]
            try:
                retval = int(i["Actor"]["Attributes"]["exitCode"])
            except:
                self._logger.exception("Cannot parse exitCode for container %s", container_id)
                retval=-1
            await ZMQUtils.send(self._docker_events_pub, EventContainerDied(container_id, retval))

    async def handle_backend_message(self, message):
        """Dispatch messages received from clients to the right handlers"""
        message_handlers = {
            BackendNewBatchJob: self.handle_new_batch_job,
            BackendNewJob: self.handle_new_job,
            BackendKillJob: self.handle_kill_job,
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._loop.create_task(func(message))

    async def handle_watcher_pipe_message(self, message):
        """Dispatch messages received from the watcher pipe to the right handlers"""
        message_handlers = {
            KWPKilledStatus: self.handle_kwp_killed_status,
            KWPRegisterContainer: self.handle_kwp_register_container
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._loop.create_task(func(message))

    async def handle_kwp_killed_status(self, message: KWPKilledStatus):
        # redirect to handle_job_closing_p2
        self._loop.create_task(self.handle_job_closing_p2(message))

    async def handle_kwp_register_container(self, message: KWPRegisterContainer):
        # ignore
        pass

    async def handle_new_batch_job(self, message: BackendNewJob):
        # TODO
        pass

    async def handle_new_job(self, message: BackendNewJob):
        self._logger.info("Received request for jobid %s", message.job_id)
        if message.debug == "ssh" and False:
            await self.send_job_result(message.job_id, "crash", 'Remote debugging is not activated on this agent.')
            return

        course_id = message.course_id
        task_id = message.task_id

        debug = message.debug
        environment_name = message.environment
        enable_network = message.enable_network
        time_limit = message.time_limit
        hard_time_limit = message.hard_time_limit or time_limit * 3
        mem_limit = message.mem_limit

        if not os.path.exists(os.path.join(self.task_directory, course_id, task_id)):
            self._logger.warning("Task %s/%s unavailable on this agent", course_id, task_id)
            await self.send_job_result(message.job_id, "crash",
                                       'Task unavailable on agent. Please retry later, the agents should synchronize soon. If the error '
                                       'persists, please contact your course administrator.')
            return

        if mem_limit < 20:
            mem_limit = 20

        if environment_name not in self._containers:
            self._logger.warning("Task %s/%s ask for an unknown environment %s (not in aliases)", course_id, task_id, environment_name)
            await self.send_job_result(message.job_id, "crash", 'Unknown container. Please contact your course administrator.')
            return
        environment = self._containers[environment_name]["id"]

        if debug == "ssh":  # allow 30 minutes of real time.
            time_limit = 30 * 60
            hard_time_limit = 30 * 60

        # Remove possibly existing older folder and creates the new ones
        internal_job_id = self._get_new_internal_job_id()
        container_path = os.path.join(self.tmp_dir, str(internal_job_id))  # tmp_dir/id/
        task_path = os.path.join(container_path, 'task')  # tmp_dir/id/task/
        sockets_path = os.path.join(container_path, 'sockets')  # tmp_dir/id/socket/
        student_path = os.path.join(task_path, 'student')  # tmp_dir/id/task/student/
        input_path = os.path.join(container_path, 'input') # tmp_dir/id/input

        try:
            rmtree(container_path)
        except:
            pass

        # Create the needed directories
        os.mkdir(container_path)
        os.mkdir(sockets_path)
        os.chmod(container_path, 0o777)
        os.chmod(sockets_path, 0o777)

        # Compute input
        container_input = {"input": message.inputdata}
        if debug:
            container_input["debug"] = debug

        with open(input_path, 'wb') as f:
            f.write(json.dumps(container_input).encode("utf8"))
        os.chmod(input_path, 0o777)

        # TODO: avoid copy
        copytree(os.path.join(self.task_directory, course_id, task_id), task_path)
        os.chmod(task_path, 0o777)

        if not os.path.exists(student_path):
            os.mkdir(student_path)
            os.chmod(student_path, 0o777)

        # Run the container
        try:
            container_id = await self._loop.run_in_executor(None, lambda :self._docker.create_container(environment, debug, enable_network,
                                                                                                        mem_limit, task_path, sockets_path,
                                                                                                        input_path))

            # TODO: run_student management
            # Start a socket to communicate between the agent and the container
            # container_set = set()
            # student_container_management_server_fact = lambda: self._get_agent_student_container_server(
            #    container_id,
            #    container_set,
            #    student_path,
            #    task.get_environment(),
            #    time_limit,
            #    mem_limit)

            # Small workaround for error "AF_UNIX path too long" when the agent is launched inside a container. Resolve all symlinks to reduce the
            # path length.
            # smaller_path_to_socket = os.path.realpath(os.path.join(sockets_path, 'INGInious.sock'))

            # server = self._loop.create_unix_server(student_container_management_server_fact, smaller_path_to_socket)
            # self._loop.create_task(server)

            # Start the container
            await self._loop.run_in_executor(None, lambda: self._docker.start_container(container_id))
        except Exception as e:
            self._logger.warning("Cannot create container! %s", str(e), exc_info=True)
            await self.send_job_result(message.job_id, "crash", 'Cannot start container')
            rmtree(container_path)
            return

        # Ask the "cgroup" thread to verify the timeout/memory limit
        await ZMQUtils.send(self._killer_watcher_push.get_push_socket(), KWPRegisterContainer(container_id, mem_limit, time_limit, hard_time_limit))

        # Store info
        self._containers_running[container_id] = message, container_path
        self._container_for_job[message.job_id] = container_id

        # Tell the backend/client the job has started
        await ZMQUtils.send(self._backend_socket, AgentJobStarted(message.job_id))

        # If ssh mode is activated, get the ssh key
        # TODO SSH Debug
        #if debug == "ssh":
        #    self._handle_container_ssh_start(docker_connection, container_id, job_id, ssh_callback)

    async def handle_job_closing_p1(self, container_id, retval):
        try:
            message, container_path = self._containers_running[container_id]
            del self._containers_running[container_id]
        except:
            self._logger.warning("Container %s that has finished(p1) was not launched by this agent", str(container_id), exc_info=True)
            return

        self._containers_ending[container_id] = (message, container_path, retval)

        await ZMQUtils.send(self._killer_watcher_push.get_push_socket(),
                            KWPKilledStatus(container_id, "killed" if container_id in self._containers_killed else None))


    async def handle_job_closing_p2(self, killed_msg: KWPKilledStatus):
        container_id = killed_msg.container_id
        try:
            message, container_path, retval = self._containers_ending[container_id]
            del self._containers_ending[container_id]
        except:
            self._logger.warning("Container %s that has finished(p2) was not launched by this agent", str(container_id))
            return

        debug = message.debug

        # TODO: debug ssh
        # if debug == "ssh":
        #     self._handle_container_ssh_close(job_id)

        result = "crash" if retval == -1 else None
        error_msg = None
        grade = None
        problems = {}
        custom = {}

        if killed_msg.killed_result is not None:
            result = killed_msg.killed_result

        # If everything did well, continue to retrieve the status from the container
        if result is None:
            # Get logs back
            try:
                return_value = await self._loop.run_in_executor(None, lambda :self._docker.get_logs(container_id))
                result = return_value.get("result", "error")
                error_msg = return_value.get("text", "")
                grade = return_value.get("grade", None)
                problems = return_value.get("problems", {})
                custom = return_value.get("custom", {})
            except Exception as e:
                self._logger.exception("Cannot get back stdout of container %s! (%s)", container_id, str(e))
                result = "crash"
                error_msg = 'The grader did not return a readable output'

        # Default values
        if error_msg is None:
            error_msg = ""
        if grade is None:
            if result == "success":
                grade = 100.0
            else:
                grade = 0.0

        # Remove container
        self._loop.run_in_executor(None, lambda : self._docker.remove_container(container_id))

        # TODO run_student
        # Remove subcontainers
        # for i in container_set:
        #    # Also deletes them from the timeout/memory watchers
        #    self._timeout_watcher.container_had_error(container_id)
        #    self._memory_watcher.container_had_error(container_id)
        #    _thread.start_new_thread(docker_connection.remove_container, (i, True, False, True))

        # Delete folders
        rmtree(container_path)

        # Return!
        await self.send_job_result(message.job_id, result, error_msg, grade, problems, custom)

        # Do not forget to remove data from internal state
        del self._container_for_job[message.job_id]
        if container_id in self._containers_killed:
            self._containers_killed.remove(container_id)

    async def handle_kill_job(self, message: BackendKillJob):
        if message.job_id in self._container_for_job:
            self._containers_killed.add(self._container_for_job[message.job_id])
            await self._loop.run_in_executor(None, self._docker.kill_container(self._container_for_job[message.job_id]))
        else:
            self._logger.warning("Cannot kill container for job %s because it is not running", str(message.job_id))

    async def handle_docker_event(self, message):
        assert type(message) == EventContainerDied
        self._loop.create_task(self.handle_job_closing_p1(message.container_id, message.retval))

    async def send_job_result(self, job_id: BackendJobId, result: str, text: str = "", grade: float = None, problems: Dict[str, SPResult] = None,
                              custom: Dict[str, Any] = None):
        if grade is None:
            if result == "success":
                grade = 100.0
            else:
                grade = 0.0
        if problems is None:
            problems = {}
        if custom is None:
            custom = {}

        await ZMQUtils.send(self._backend_socket, AgentJobDone(job_id, (result, text), grade, problems, custom))

    async def run_dealer(self):
        self._backend_socket.connect(self._backend_addr)

        # Init Docker events watcher
        await self.init_watch_docker_events()

        # Init watcher pipe
        await self.init_watcher_pipe()

        # Tell the backend we are up and have `nb_sub_agents` threads available

        await ZMQUtils.send(self._backend_socket, AgentHello(self._nb_sub_agents, self._containers, self._batch_containers))

        # And then run the agent
        try:
            while True:
                socks = await self._poller.poll()
                socks = dict(socks)

                # New message from backend
                if self._backend_socket in socks:
                    message = await ZMQUtils.recv(self._backend_socket)
                    await self.handle_backend_message(message)

                # New docker event
                if self._docker_events_sub in socks:
                    message = await ZMQUtils.recv(self._docker_events_sub)
                    await self.handle_docker_event(message)

                # End of watcher pipe
                if self._killer_watcher_pull.get_pull_socket() in socks:
                    message = await ZMQUtils.recv(self._killer_watcher_pull.get_pull_socket())
                    await self.handle_watcher_pipe_message(message)

        except asyncio.CancelledError:
            return
        except KeyboardInterrupt:
            return

    def _get_new_internal_job_id(self):
        """ Get a new internal job id """
        internal_job_id = self._internal_job_count
        self._internal_job_count += 1
        return internal_job_id
