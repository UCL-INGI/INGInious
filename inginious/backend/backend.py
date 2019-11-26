# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import asyncio
import logging
import queue
import time
import zmq
from zmq.asyncio import Poller

from inginious.common.message_meta import ZMQUtils
from inginious.common.messages import BackendNewJob, AgentJobStarted, AgentJobDone, AgentJobSSHDebug, \
    BackendJobDone, BackendJobStarted, BackendJobSSHDebug, ClientNewJob, ClientKillJob, BackendKillJob, AgentHello, ClientHello, \
    BackendUpdateEnvironments, Unknown, Ping, Pong, ClientGetQueue, BackendGetQueue


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

        # Enable support for ipv6
        self._agent_socket.ipv6 = True
        self._client_socket.ipv6 = True

        self._poller = Poller()
        self._poller.register(self._agent_socket, zmq.POLLIN)
        self._poller.register(self._client_socket, zmq.POLLIN)

        # List of environments available
        # {
        #     "name": ("last_id", "created_last", ["agent_addr1", "agent_addr2"], "type")
        # }
        self._environments = {}
        self._registered_clients = set()  # addr of registered clients
        self._registered_agents = {}  # addr of registered agents
        self._available_agents = []  # addr of available agents
        self._ping_count = {}  # ping count per addr of agents
        self._waiting_jobs_pq = queue.PriorityQueue() # priority queue for waiting jobs
        self._waiting_jobs = {}  # mapping job to job message, with key: [(client_addr_as_bytes, ClientNewJob])]
        self._job_running = {}  # indicates on which agent which job is running. format: {BackendJobId:(addr_as_bytes,ClientNewJob,start_time)}

    async def handle_agent_message(self, agent_addr, message):
        """Dispatch messages received from agents to the right handlers"""
        message_handlers = {
            AgentHello: self.handle_agent_hello,
            AgentJobStarted: self.handle_agent_job_started,
            AgentJobDone: self.handle_agent_job_done,
            AgentJobSSHDebug: self.handle_agent_job_ssh_debug,
            Pong: self._handle_pong
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._create_safe_task(func(agent_addr, message))

    async def handle_client_message(self, client_addr, message):
        """Dispatch messages received from clients to the right handlers"""

        # Verify that the client is registered
        if message.__class__ != ClientHello and client_addr not in self._registered_clients:
            await ZMQUtils.send_with_addr(self._client_socket, client_addr, Unknown())
            return

        message_handlers = {
            ClientHello: self.handle_client_hello,
            ClientNewJob: self.handle_client_new_job,
            ClientKillJob: self.handle_client_kill_job,
            ClientGetQueue: self.handle_client_get_queue,
            Ping: self.handle_client_ping
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._create_safe_task(func(client_addr, message))

    async def send_environment_update_to_client(self, client_addrs):
        """ :param client_addrs: list of clients to which we should send the update """
        self._logger.debug("Sending environments updates...")
        available_environments = {idx: environment[3] for idx, environment in self._environments.items()}
        msg = BackendUpdateEnvironments(available_environments)
        for client in client_addrs:
            await ZMQUtils.send_with_addr(self._client_socket, client, msg)

    async def handle_client_hello(self, client_addr, _: ClientHello):
        """ Handle an ClientHello message. Send available environments to the client """
        self._logger.info("New client connected %s", client_addr)
        self._registered_clients.add(client_addr)
        await self.send_environment_update_to_client([client_addr])

    async def handle_client_ping(self, client_addr, _: Ping):
        """ Handle an Ping message. Pong the client """
        await ZMQUtils.send_with_addr(self._client_socket, client_addr, Pong())

    async def handle_client_new_job(self, client_addr, message: ClientNewJob):
        """ Handle an ClientNewJob message. Add a job to the queue and triggers an update """
        self._logger.info("Adding a new job %s %s to the queue", client_addr, message.job_id)

        job = (message.priority, time.time(), client_addr, message.job_id, message)
        self._waiting_jobs[(client_addr, message.job_id)] = job
        self._waiting_jobs_pq.put(job)

        await self.update_queue()

    async def handle_client_kill_job(self, client_addr, message: ClientKillJob):
        """ Handle an ClientKillJob message. Remove a job from the waiting list or send the kill message to the right agent. """
        # Check if the job is not in the queue
        if (client_addr, message.job_id) in self._waiting_jobs:

            # Erase the job reference in priority queue
            job = self._waiting_jobs.pop((client_addr, message.job_id))
            job[-1] = None

            # Do not forget to send a JobDone
            await ZMQUtils.send_with_addr(self._client_socket, client_addr, BackendJobDone(message.job_id, ("killed", "You killed the job"),
                                                                                           0.0, {}, {}, {}, "", None, "", ""))
        # If the job is running, transmit the info to the agent
        elif (client_addr, message.job_id) in self._job_running:
            agent_addr = self._job_running[(client_addr, message.job_id)][0]
            await ZMQUtils.send_with_addr(self._agent_socket, agent_addr, BackendKillJob((client_addr, message.job_id)))
        else:
            self._logger.warning("Client %s attempted to kill unknown job %s", str(client_addr), str(message.job_id))

    async def handle_client_get_queue(self, client_addr, _: ClientGetQueue):
        """ Handles a ClientGetQueue message. Send back info about the job queue"""
        #jobs_running: a list of tuples in the form
        #(job_id, is_current_client_job, agent_name, info, launcher, started_at, max_time)
        jobs_running = list()

        for backend_job_id, content in self._job_running.items():
            jobs_running.append((content[1].job_id, backend_job_id[0] == client_addr, self._registered_agents[content[0]],
                                 content[1].course_id+"/"+content[1].task_id,
                                 content[1].launcher, int(content[2]), self._get_time_limit_estimate(content[1])))

        #jobs_waiting: a list of tuples in the form
        #(job_id, is_current_client_job, info, launcher, max_time)
        jobs_waiting = list()

        for job_client_addr, job in self._waiting_jobs.items():
            msg = job[-1]
            if isinstance(msg, ClientNewJob):
                jobs_waiting.append((msg.job_id, job_client_addr[0] == client_addr, msg.course_id+"/"+msg.task_id, msg.launcher,
                                     self._get_time_limit_estimate(msg)))

        await ZMQUtils.send_with_addr(self._client_socket, client_addr, BackendGetQueue(jobs_running, jobs_waiting))

    async def update_queue(self):
        """
        Send waiting jobs to available agents
        """

        # Loop on available agents to maximize running jobs, and break if priority queue empty
        for i in range(0, len(self._available_agents)):
            if self._waiting_jobs_pq.empty():
                break

            priority, insert_time, client_addr, job_id, job_msg = self._waiting_jobs_pq.get()

            # Killed job, removing it from the mapping
            if not job_msg:
                del self._waiting_jobs[(client_addr, job_id)]
                continue

            # Find agents that can run this job
            possible_agents = list(set(self._environments[job_msg.environment][2]).intersection(set(self._available_agents)))

            # No agent available, put job back to queue with lower priority
            if not possible_agents:
                job = (priority+1, insert_time, client_addr, job_id, job_msg)
                self._waiting_jobs_pq.put(job)
                self._logger.warning("No agent for job id %s, putting it back in the queue.", job_id)
                continue

            # Agent chosen, removing it from availability list
            agent_addr = possible_agents[0]
            self._available_agents.remove(agent_addr)

            # Remove the job from the queue
            del self._waiting_jobs[(client_addr, job_id)]

            # Send the job to agent
            job_id = (client_addr, job_msg.job_id)
            self._job_running[job_id] = (agent_addr, job_msg, time.time())
            self._logger.info("Sending job %s %s to agent %s", client_addr, job_msg.job_id, agent_addr)
            await ZMQUtils.send_with_addr(self._agent_socket, agent_addr, BackendNewJob(job_id, job_msg.course_id, job_msg.task_id,
                                                                                        job_msg.inputdata, job_msg.environment,
                                                                                        job_msg.environment_parameters,
                                                                                        job_msg.debug))

    async def handle_agent_hello(self, agent_addr, message: AgentHello):
        """
        Handle an AgentAvailable message. Add agent_addr to the list of available agents
        """
        self._logger.info("Agent %s (%s) said hello", agent_addr, message.friendly_name)

        if agent_addr in self._registered_agents:
            # Delete previous instance of this agent, if any
            await self._delete_agent(agent_addr)

        self._registered_agents[agent_addr] = message.friendly_name
        self._available_agents.extend([agent_addr for _ in range(0, message.available_job_slots)])
        self._ping_count[agent_addr] = 0

        # update information about available environments
        for environment_name, environment_info in message.available_environments.items():
            if environment_name in self._environments:
                # check if the id is the same
                if self._environments[environment_name][0] == environment_info["id"]:
                    # ok, just add the agent to the list of agents that have the environment
                    self._logger.debug("Registering environment %s for agent %s", environment_name, str(agent_addr))
                    self._environments[environment_name][2].append(agent_addr)
                elif self._environments[environment_name][1] > environment_info["created"]:
                    # environments stored have been created after the new one
                    # add the agent, but emit a warning
                    self._logger.warning("Environment %s has multiple version: \n"
                                         "\t Currently registered agents have version %s (%i)\n"
                                         "\t New agent %s has version %s (%i)",
                                         environment_name,
                                         self._environments[environment_name][0], self._environments[environment_name][1],
                                         str(agent_addr), environment_info["id"], environment_info["created"])
                    self._environments[environment_name][2].append(agent_addr)
                else:  # self._environments[environment_name][1] < environment_info["created"]:
                    # environments stored have been created before the new one
                    # add the agent, update the infos, and emit a warning
                    self._logger.warning("Environment %s has multiple version: \n"
                                         "\t Currently registered agents have version %s (%i)\n"
                                         "\t New agent %s has version %s (%i)",
                                         environment_name,
                                         self._environments[environment_name][0], self._environments[environment_name][1],
                                         str(agent_addr), environment_info["id"], environment_info["created"])
                    self._environments[environment_name] = (environment_info["id"], environment_info["created"],
                                                        self._environments[environment_name][2] + [agent_addr],
                                                        environment_info["type"])
            else:
                # just add it
                self._logger.debug("Registering environment %s for agent %s", environment_name, str(agent_addr))
                self._environments[environment_name] = (environment_info["id"], environment_info["created"], [agent_addr],
                                                    environment_info["type"])

        # update the queue
        await self.update_queue()

        # update clients
        await self.send_environment_update_to_client(self._registered_clients)

    async def handle_agent_job_started(self, agent_addr, message: AgentJobStarted):
        """Handle an AgentJobStarted message. Send the data back to the client"""
        self._logger.debug("Job %s %s started on agent %s", message.job_id[0], message.job_id[1], agent_addr)
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendJobStarted(message.job_id[1]))

    async def handle_agent_job_done(self, agent_addr, message: AgentJobDone):
        """Handle an AgentJobDone message. Send the data back to the client, and start new job if needed"""

        if agent_addr in self._registered_agents:
            self._logger.info("Job %s %s finished on agent %s", message.job_id[0], message.job_id[1], agent_addr)

            # Remove the job from the list of running jobs
            del self._job_running[message.job_id]

            # Sent the data back to the client
            await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendJobDone(message.job_id[1], message.result,
                                                                                                 message.grade, message.problems,
                                                                                                 message.tests, message.custom,
                                                                                                 message.state, message.archive,
                                                                                                 message.stdout, message.stderr))

            # The agent is available now
            self._available_agents.append(agent_addr)
        else:
            self._logger.warning("Job result %s %s from non-registered agent %s", message.job_id[0], message.job_id[1], agent_addr)

        # update the queue
        await self.update_queue()

    async def handle_agent_job_ssh_debug(self, _, message: AgentJobSSHDebug):
        """Handle an AgentJobSSHDebug message. Send the data back to the client"""
        await ZMQUtils.send_with_addr(self._client_socket, message.job_id[0], BackendJobSSHDebug(message.job_id[1], message.host, message.port,
                                                                                                 message.password))

    async def run(self):
        self._logger.info("Backend started")
        self._agent_socket.bind(self._agent_addr)
        self._client_socket.bind(self._client_addr)
        self._loop.call_later(1, self._create_safe_task, self._do_ping())

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

    async def _handle_pong(self, agent_addr, _ : Pong):
        """ Handle a pong """
        self._ping_count[agent_addr] = 0

    async def _do_ping(self):
        """ Ping the agents """

        # the list() call here is needed, as we remove entries from _registered_agents!
        for agent_addr, friendly_name in list(self._registered_agents.items()):
            try:
                ping_count = self._ping_count.get(agent_addr, 0)
                if ping_count > 5:
                    self._logger.warning("Agent %s (%s) does not respond: removing from list.", agent_addr, friendly_name)
                    delete_agent = True
                else:
                    self._ping_count[agent_addr] = ping_count + 1
                    await ZMQUtils.send_with_addr(self._agent_socket, agent_addr, Ping())
                    delete_agent = False
            except:
                # This should not happen, but it's better to check anyway.
                self._logger.exception("Failed to send ping to agent %s (%s). Removing it from list.", agent_addr, friendly_name)
                delete_agent = True

            if delete_agent:
                try:
                    await self._delete_agent(agent_addr)
                except:
                    self._logger.exception("Failed to delete agent %s (%s)!", agent_addr, friendly_name)

        self._loop.call_later(1, self._create_safe_task, self._do_ping())

    async def _delete_agent(self, agent_addr):
        """ Deletes an agent """
        self._available_agents = [agent for agent in self._available_agents if agent != agent_addr]
        del self._registered_agents[agent_addr]
        await self._recover_jobs(agent_addr)

    async def _recover_jobs(self, agent_addr):
        """ Recover the jobs sent to a crashed agent """
        for (client_addr, job_id), (agent, job_msg, _) in reversed(list(self._job_running.items())):
            if agent == agent_addr:
                await ZMQUtils.send_with_addr(self._client_socket, client_addr,
                                              BackendJobDone(job_id, ("crash", "Agent restarted"),
                                                             0.0, {}, {}, {}, "", None, None, None))
                del self._job_running[(client_addr, job_id)]

        await self.update_queue()

    def _create_safe_task(self, coroutine):
        """ Calls self._loop.create_task with a safe (== with logged exception) coroutine """
        task = self._loop.create_task(coroutine)
        task.add_done_callback(self.__log_safe_task)
        return task

    def __log_safe_task(self, task):
        exception = task.exception()
        if exception is not None:
            self._logger.exception("An exception occurred while running a Task", exc_info=exception)

    def _get_time_limit_estimate(self, job_info: ClientNewJob):
        """
            Returns an estimate of the time taken by a given job, if available in the environment_parameters.
            For this to work, ["limits"]["time"] must be a parameter of the environment.
        """
        try:
            return int(job_info.environment_parameters["limits"]["time"])
        except:
            return -1 # unknown