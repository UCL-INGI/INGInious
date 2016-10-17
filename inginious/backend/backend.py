# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import asyncio
import logging
from collections import OrderedDict

import zmq
from zmq.asyncio import Poller

from inginious.common.message_meta import ZMQUtils
from inginious.common.messages import BackendNewJob, AgentJobStarted, AgentBatchJobStarted, AgentBatchJobDone, AgentJobDone, AgentJobSSHDebug, \
    BackendJobDone, BackendJobStarted, BackendJobSSHDebug, BackendBatchJobStarted, BackendBatchJobDone, ClientNewJob, ClientNewBatchJob, \
    BackendNewBatchJob, ClientKillJob, BackendKillJob, AgentHello, ClientHello, BackendUpdateContainers, Unknown, Ping, Pong


class Backend(object):
    """
        Backend. Central point of the architecture, manages communication between clients (frontends) and agents.
        Schedule jobs on agents.
    """

    def __init__(self, context, agent_addr, client_addr):
        self._content = context
        self._loop = asyncio.get_event_loop()
        self._agent_addr = agent_addr
        self._client_addr = client_addr

        self._agent_socket = context.socket(zmq.ROUTER)
        self._client_socket = context.socket(zmq.ROUTER)
        self._logger = logging.getLogger("inginious.backend")

        self._poller = Poller()
        self._poller.register(self._agent_socket, zmq.POLLIN)
        self._poller.register(self._client_socket, zmq.POLLIN)

        # List of containers available
        # {
        #     "name": ("last_id", "created_last", ["agent_addr1", "agent_addr2"])
        # }
        self._containers = {}

        # List of batch containers available
        # {
        #   "name": {
        #       "description": "a description written in RST",
        #       "id": "container img id",
        #       "created": 123456789,
        #       "agents": ["agent_addr1", "agent_addr2"]
        #       "parameters": {
        #       "key": {
        #           "type:" "file",  # or "text",
        #           "path": "path/to/file/inside/input/dir",  # not mandatory in file, by default "key"
        #           "name": "name of the field",  # not mandatory in file, default "key"
        #           "description": "a short description of what this field is used for"  # not mandatory, default ""
        #       }
        #   }
        # }
        self._batch_containers = {}

        # Batch containers available per agent {"agent_addr": ["batch_id_1", ...]}
        self._batch_containers_on_agent = {}

        # Containers available per agent {"agent_addr": ["container_id_1", ...]}
        self._containers_on_agent = {}

        self._registered_clients = set()  # addr of registered clients
        self._available_agents = []  # addr of available agents
        self._waiting_jobs = OrderedDict()  # rb queue for waiting jobs format:[(client_addr_as_bytes, Union[ClientNewJob,ClientNewBatchJob])]
        self._job_running = {}  # indicates on which agent which job is running. format: {BackendJobId:addr_as_bytes}
        self._batch_job_running = {}  # indicates on which agent which job is running. format: {BackendJobId:addr_as_bytes}

    async def handle_agent_message(self, agent_addr, message):
        """Dispatch messages received from agents to the right handlers"""
        message_handlers = {
            AgentHello: self.handle_agent_hello,
            AgentBatchJobStarted: self.handle_agent_batch_job_started,
            AgentBatchJobDone: self.handle_agent_batch_job_done,
            AgentJobStarted: self.handle_agent_job_started,
            AgentJobDone: self.handle_agent_job_done,
            AgentJobSSHDebug: self.handle_agent_job_ssh_debug,
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._loop.create_task(func(agent_addr, message))

    async def handle_client_message(self, client_addr, message):
        """Dispatch messages received from clients to the right handlers"""

        # Verify that the client is registered
        if message.__class__ != ClientHello and client_addr not in self._registered_clients:
            await ZMQUtils.send_with_addr(self._client_socket, client_addr, Unknown())
            return

        message_handlers = {
            ClientHello: self.handle_client_hello,
            ClientNewBatchJob: self.handle_client_new_batch_job,
            ClientNewJob: self.handle_client_new_job,
            ClientKillJob: self.handle_client_kill_job,
            Ping: self.handle_client_ping
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._loop.create_task(func(client_addr, message))

    async def send_container_update_to_client(self, client_addrs):
        """ :param client_addrs: list of clients to which we should send the update """
        self._logger.debug("Sending containers updates...")
        available_containers = tuple(self._containers.keys())
        available_batch_containers = {x: {"description": y["description"], "parameters": y["parameters"]} for x, y in self._batch_containers.items()}
        msg = BackendUpdateContainers(available_containers, available_batch_containers)
        for client in client_addrs:
            await ZMQUtils.send_with_addr(self._client_socket, client, msg)

    async def handle_client_hello(self, client_addr, _: ClientHello):
        """ Handle an ClientHello message. Send available (batch) containers to the client """
        self._logger.info("New client connected %s", client_addr)
        self._registered_clients.add(client_addr)
        await self.send_container_update_to_client([client_addr])

    async def handle_client_ping(self, client_addr, _: Ping):
        """ Handle an Ping message. Pong the client """
        await ZMQUtils.send_with_addr(self._client_socket, client_addr, Pong())

    async def handle_client_new_batch_job(self, client_addr, message: ClientNewBatchJob):
        """ Handle an ClientNewBatchJob message. Add a job to the queue and triggers an update """
        self._logger.info("Adding a new batch job %s %s to the queue", client_addr, message.job_id)
        self._waiting_jobs[(client_addr, message.job_id, "batch")] = message
        await self.update_queue()

    async def handle_client_new_job(self, client_addr, message: ClientNewJob):
        """ Handle an ClientNewJob message. Add a job to the queue and triggers an update """
        self._logger.info("Adding a new job %s %s to the queue", client_addr, message.job_id)
        self._waiting_jobs[(client_addr, message.job_id, "grade")] = message
        await self.update_queue()

    async def handle_client_kill_job(self, client_addr, message: ClientKillJob):
        """ Handle an ClientKillJob message. Remove a job from the waiting list or send the kill message to the right agent. """
        # Check if the job is not in the queue
        if (client_addr, message.job_id, "grade") in self._waiting_jobs:
            del self._waiting_jobs[(client_addr, message.job_id, "grade")]
            # Do not forget to send a JobDone
            await ZMQUtils.send_with_addr(self._client_socket, client_addr, BackendJobDone(message.job_id, ("killed", "You killed the job"),
                                                                                           0, {}, {}, {}, None, "", ""))
        # If the job is running, transmit the info to the agent
        elif (client_addr, message.job_id) in self._job_running:
            agent_addr = self._job_running[(client_addr, message.job_id)]
            await ZMQUtils.send_with_addr(self._agent_socket, agent_addr, BackendKillJob((client_addr, message.job_id)))
        else:
            self._logger.warning("Client %s attempted to kill unknown job %s", str(client_addr), str(message.job_id))

    async def update_queue(self):
        """
        Send waiting jobs to available agents
        """

        # For now, round-robin
        not_found_for_agent = []

        while len(self._available_agents) > 0 and len(self._waiting_jobs) > 0:
            agent_addr = self._available_agents.pop(0)

            # Find first job that can be run on this agent
            found = False
            client_addr, job_id, typestr, job_msg = None, None, None, None
            for (client_addr, job_id, typestr), job_msg in self._waiting_jobs.items():
                if typestr == "batch" and job_msg.container_name in self._batch_containers_on_agent[agent_addr]:
                    found = True
                    break
                elif typestr == "grade" and job_msg.environment in self._containers_on_agent[agent_addr]:
                    found = True
                    break

            if not found:
                self._logger.debug("Nothing to do for agent %s", agent_addr)
                not_found_for_agent.append(agent_addr)
                continue

            # Remove the job from the queue
            del self._waiting_jobs[(client_addr, job_id, typestr)]

            if typestr == "grade" and isinstance(job_msg, ClientNewJob):
                job_id = (client_addr, job_msg.job_id)
                self._job_running[job_id] = agent_addr
                self._logger.info("Sending job %s %s to agent %s", client_addr, job_msg.job_id, agent_addr)
                await ZMQUtils.send_with_addr(self._agent_socket, agent_addr, BackendNewJob(job_id, job_msg.course_id, job_msg.task_id,
                                                                                            job_msg.inputdata, job_msg.environment,
                                                                                            job_msg.enable_network, job_msg.time_limit,
                                                                                            job_msg.hard_time_limit, job_msg.mem_limit,
                                                                                            job_msg.debug))
            elif typestr == "batch":
                job_id = (client_addr, job_msg.job_id)
                self._batch_job_running[job_id] = agent_addr
                self._logger.info("Sending batch job %s %s to agent %s", client_addr, job_msg.job_id, agent_addr)
                await ZMQUtils.send_with_addr(self._agent_socket, agent_addr, BackendNewBatchJob(job_id, job_msg.container_name, job_msg.input_data))

        # Do not forget to add again for which we did not find jobs to do
        self._available_agents += not_found_for_agent

    async def handle_agent_hello(self, agent_addr, message: AgentHello):
        """
        Handle an AgentAvailable message. Add agent_addr to the list of available agents
        """
        self._logger.info("Agent %s said hello", agent_addr)

        for i in range(0, message.available_job_slots):
            self._available_agents.append(agent_addr)

        self._batch_containers_on_agent[agent_addr] = message.available_batch_containers.keys()
        self._containers_on_agent[agent_addr] = message.available_containers.keys()

        # update information about available containers
        for container_name, container_info in message.available_containers.items():
            if container_name in self._containers:
                # check if the id is the same
                if self._containers[container_name][0] == container_info["id"]:
                    # ok, just add the agent to the list of agents that have the container
                    self._logger.debug("Registering container %s for agent %s", container_name, str(agent_addr))
                    self._containers[container_name][2].append(agent_addr)
                elif self._containers[container_name][1] > container_info["created"]:
                    # containers stored have been created after the new one
                    # add the agent, but emit a warning
                    self._logger.warning("Container %s has multiple version: \n"
                                         "\t Currently registered agents have version %s (%i)\n"
                                         "\t New agent %s has version %s (%i)",
                                         container_name,
                                         self._containers[container_name][0], self._containers[container_name][1],
                                         str(agent_addr), container_info["id"], container_info["created"])
                    self._containers[container_name][2].append(agent_addr)
                else:  # self._containers[container_name][1] < container_info["created"]:
                    # containers stored have been created before the new one
                    # add the agent, update the infos, and emit a warning
                    self._logger.warning("Container %s has multiple version: \n"
                                         "\t Currently registered agents have version %s (%i)\n"
                                         "\t New agent %s has version %s (%i)",
                                         container_name,
                                         self._containers[container_name][0], self._containers[container_name][1],
                                         str(agent_addr), container_info["id"], container_info["created"])
                    self._containers[container_name] = (container_info["id"], container_info["created"],
                                                        self._containers[container_name][2] + [agent_addr])
            else:
                # just add it
                self._logger.debug("Registering container %s for agent %s", container_name, str(agent_addr))
                self._containers[container_name] = (container_info["id"], container_info["created"], [agent_addr])

        # update information about available batch containers
        for container_name, container_info in message.available_batch_containers.items():
            if container_name in self._batch_containers:
                if self._batch_containers[container_name]["id"] == container_info["id"]:
                    # just add it
                    self._logger.debug("Registering batch container %s for agent %s", container_name, str(agent_addr))
                    self._batch_containers[container_name]["agents"].append(agent_addr)
                elif self._containers[container_name]["created"] > container_info["created"]:
                    # containers stored have been created after the new one
                    # add the agent, but emit a warning
                    self._logger.warning("Batch container %s has multiple version: \n"
                                         "\t Currently registered agents have version %s (%i)\n"
                                         "\t New agent %s has version %s (%i)",
                                         container_name,
                                         self._containers[container_name]["id"], self._containers[container_name]["created"],
                                         str(agent_addr), container_info["id"], container_info["created"])
                    self._containers[container_name]["agents"].append(agent_addr)
                else:  # self._containers[container_name]["created"] < container_info["created"]:
                    # containers stored have been created before the new one
                    # add the agent, but emit a warning
                    self._logger.warning("Batch container %s has multiple version: \n"
                                         "\t Currently registered agents have version %s (%i)\n"
                                         "\t New agent %s has version %s (%i)",
                                         container_name,
                                         self._containers[container_name]["id"], self._containers[container_name]["created"],
                                         str(agent_addr), container_info["id"], container_info["created"])
                    old_agents = self._containers[container_name]["agents"]
                    self._containers[container_name] = container_info.copy()
                    self._batch_containers[container_name]["agents"] = old_agents + [agent_addr]
            else:
                # just add it
                self._logger.debug("Registering batch container %s for agent %s", container_name, str(agent_addr))
                self._batch_containers[container_name] = container_info.copy()
                self._batch_containers[container_name]["agents"] = [agent_addr]

        # update the queue
        await self.update_queue()

        # update clients
        await self.send_container_update_to_client(self._registered_clients)

    async def handle_agent_job_started(self, agent_addr, message: AgentJobStarted):
        """Handle an AgentJobStarted message. Send the data back to the client"""
        self._logger.debug("job %s %s started on agent %s", message.job_id[0], message.job_id[1], agent_addr)
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendJobStarted(message.job_id[1]))

    async def handle_agent_job_done(self, agent_addr, message: AgentJobDone):
        """Handle an AgentJobDone message. Send the data back to the client, and start new job if needed"""

        self._logger.debug("job %s %s finished on agent %s", message.job_id[0], message.job_id[1], agent_addr)

        # Remove the job from the list of running jobs
        del self._job_running[message.job_id]

        # Sent the data back to the client
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendJobDone(message.job_id[1], message.result,
                                                                                             message.grade, message.problems,
                                                                                             message.tests, message.custom, message.archive,
                                                                                             message.stdout, message.stderr))

        # The agent is available now
        self._available_agents.append(agent_addr)

        # update the queue
        await self.update_queue()

    async def handle_agent_job_ssh_debug(self, _, message: AgentJobSSHDebug):
        """Handle an AgentJobSSHDebug message. Send the data back to the client"""
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendJobSSHDebug(message.job_id[1], message.host, message.port,
                                                                                                 message.password))

    async def handle_agent_batch_job_started(self, agent_addr, message: AgentBatchJobStarted):
        """Handle an AgentBatchJobStarted message. Send the data back to the client"""
        self._logger.debug("batch job %s %s started on agent %s", message.job_id[0], message.job_id[1], agent_addr)
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendBatchJobStarted(message.job_id[1]))

    async def handle_agent_batch_job_done(self, agent_addr, message: AgentBatchJobDone):
        """Handle an AgentBatchJobDone message. Send the data back to the client, and start new job if needed"""

        self._logger.debug("batch job %s %s finished on agent %s", message.job_id[0], message.job_id[1], agent_addr)

        # Remove the job from the list of running jobs
        del self._batch_job_running[message.job_id]

        # Sent the data back to the client
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendBatchJobDone(message.job_id[1], message.retval,
                                                                                                  message.stdout, message.stderr, message.file))

        # The agent is available now
        self._available_agents.append(agent_addr)

        # update the queue
        await self.update_queue()

    async def run(self):
        self._logger.info("Backend started")
        self._agent_socket.bind(self._agent_addr)
        self._client_socket.bind(self._client_addr)

        try:
            while True:
                socks = await self._poller.poll()
                socks = dict(socks)

                # New message from agent
                if self._agent_socket in socks:
                    agent_addr, message = await ZMQUtils.recv_with_addr(self._agent_socket)
                    await self.handle_agent_message(agent_addr, message)

                # New message from client
                if self._client_socket in socks:
                    client_addr, message = await ZMQUtils.recv_with_addr(self._client_socket)
                    await self.handle_client_message(client_addr, message)

        except asyncio.CancelledError:
            return
        except KeyboardInterrupt:
            return
