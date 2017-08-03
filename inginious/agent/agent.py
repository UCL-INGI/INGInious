# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import asyncio
import logging
import os
from abc import abstractproperty, ABCMeta, abstractmethod
from typing import Dict, Any, Optional

import zmq

from inginious.common.message_meta import ZMQUtils
from inginious.common.messages import AgentHello, BackendJobId, SPResult, AgentJobDone, BackendNewJob, BackendKillJob, \
    AgentJobStarted, AgentJobSSHDebug, Ping, Pong

"""
Various utils to implements new kind of agents easily.
"""


class CannotCreateJobException(Exception):
    """
    Exception that should be raised when a (batch or std) job cannot be created in Agent.new_job or Agent.new_batch_job
    """
    def __init__(self, message):
        self.message = message
        super(CannotCreateJobException, self).__init__()


class TooManyCallsException(Exception):
    """
    Exception raised by the Agent when the function send_ssh_job_info has been called more than once
    """
    pass


class JobNotRunningException(Exception):
    """
    Exception raised by the Agent when the functions send_job_result/send_ssh_job_info are called but the job is not running anymore
    """
    pass


class Agent(object, metaclass=ABCMeta):
    """
    An INGInious agent, that grades specific kinds of jobs, and interacts with a Backend.
    """

    def __init__(self, context, backend_addr, friendly_name, concurrency, tasks_filesystem):
        """
        :param context: a ZMQ context to which the agent will be linked
        :param backend_addr: address of the backend to which the agent should connect. The format is the same as ZMQ
        :param concurrency: number of simultaneous jobs that can be run by this agent
        :param tasks_filesystem: FileSystemProvider to the course/tasks
        """
        # These fields can be read/modified/overridden in subclasses
        self._logger = logging.getLogger("inginious.agent")
        self._loop = asyncio.get_event_loop()
        self._tasks_filesystem = tasks_filesystem

        # These fields should not be read/modified/overridden in subclasses
        self.__concurrency = concurrency

        self.__backend_addr = backend_addr
        self.__context = context
        self.__friendly_name = friendly_name
        self.__backend_socket = self.__context.socket(zmq.DEALER)
        self.__backend_socket.ipv6 = True

        self.__running_job = {}
        self.__running_batch_job = set()

    @property
    @abstractmethod
    def environments(self):
        """
        :return: a dict of available environments (containers most of the time) in the form
            {
                "name": {                          #for example, "default"
                    "id": "container img id",      #             "sha256:715c5cb5575cdb2641956e42af4a53e69edf763ce701006b2c6e0f4f39b68dd3"
                    "created": 12345678            # create date, as an unix timestamp
                }
            }

            If the environments are not containers, fills `created` with a fixed date (that will be shared by all agents of the same version),
            that could be 0. `id` can be anything, but should also be the same for the same versions of environments.

            Only the `name` field is shared with the Clients.
        """
        return {}

    async def run(self):
        """
        Runs the agent. Answer to the requests made by the Backend.
        """
        self._logger.info("Agent started")
        self.__backend_socket.connect(self.__backend_addr)

        # Tell the backend we are up and have `concurrency` threads available
        self._logger.info("Saying hello to the backend")
        await ZMQUtils.send(self.__backend_socket, AgentHello(self.__friendly_name, self.__concurrency, self.environments))

        try:
            while True:
                message = await ZMQUtils.recv(self.__backend_socket)
                await self._handle_backend_message(message)
        except asyncio.CancelledError:
            return
        except KeyboardInterrupt:
            return

    async def _handle_backend_message(self, message):
        """ Dispatch messages received from clients to the right handlers """
        message_handlers = {
            BackendNewJob: self._handle_new_job,
            BackendKillJob: self.kill_job,
            Ping: self.handle_ping
        }
        try:
            func = message_handlers[message.__class__]
        except:
            raise TypeError("Unknown message type %s" % message.__class__)
        self._loop.create_task(func(message))

    async def handle_ping(self, _ : Ping):
        """ Handle a Ping message. Pong the backend """
        await ZMQUtils.send(self.__backend_socket, Pong())

    async def _handle_new_job(self, message: BackendNewJob):
        self._logger.info("Received request for jobid %s", message.job_id)

        # For send_job_result internal checks
        self.__running_job[message.job_id] = False  # no ssh info sent

        # Tell the backend we started running the job
        await ZMQUtils.send(self.__backend_socket, AgentJobStarted(message.job_id))

        try:
            if message.environment not in self.environments:
                self._logger.warning("Task %s/%s ask for an unknown environment %s (not in aliases)", message.course_id, message.task_id,
                                     message.environment)
                raise CannotCreateJobException('This environment is not available in this agent. Please contact your course administrator.')

            task_fs = self._tasks_filesystem.from_subfolder(message.course_id).from_subfolder(message.task_id)
            if not task_fs.exists():
                self._logger.warning("Task %s/%s unavailable on this agent", message.course_id, message.task_id)
                raise CannotCreateJobException('Task unavailable on agent. Please retry later, the agents should synchronize soon. If the error '
                                               'persists, please contact your course administrator.')

            # Let the subclass run the job
            await self.new_job(message)
        except CannotCreateJobException as e:
            await self.send_job_result(message.job_id, "crash", e.message)
        except TooManyCallsException:
            self._logger.exception("TooManyCallsException in new_job")
            await self.send_job_result(message.job_id, "crash", "An unknown error occured in the agent. Please contact your course "
                                                                "administrator.")
        except JobNotRunningException:
            self._logger.exception("JobNotRunningException in new_job")
        except:
            self._logger.exception("Unknown exception in new_job")
            await self.send_job_result(message.job_id, "crash", "An unknown error occured in the agent. Please contact your course "
                                                                "administrator.")

    async def send_ssh_job_info(self, job_id: BackendJobId, host: str, port: int, key: str):
        """
        Send info about the SSH debug connection to the backend/client. Must be called *at most once* for each job.
        :exception JobNotRunningException: is raised when the job is not running anymore (send_job_result already called)
        :exception TooManyCallsException: is raised when this function has been called more than once
        """
        if job_id not in self.__running_job:
            raise JobNotRunningException()
        if self.__running_job[job_id]:
            raise TooManyCallsException()
        self.__running_job[job_id] = True  # now we have sent ssh info
        await ZMQUtils.send(self.__backend_socket, AgentJobSSHDebug(job_id, host, port, key))

    async def send_job_result(self, job_id: BackendJobId, result: str, text: str = "", grade: float = None, problems: Dict[str, SPResult] = None,
                              tests: Dict[str, Any] = None, custom: Dict[str, Any] = None, archive: Optional[bytes] = None,
                              stdout: Optional[str] = None, stderr: Optional[str] = None):
        """
        Send the result of a job back to the backend. Must be called *once and only once* for each job
        :exception JobNotRunningException: is raised when send_job_result is called more than once for a given job_id
        """
        if job_id not in self.__running_job:
            raise JobNotRunningException()
        del self.__running_job[job_id]

        if grade is None:
            if result == "success":
                grade = 100.0
            else:
                grade = 0.0
        if problems is None:
            problems = {}
        if custom is None:
            custom = {}
        if tests is None:
            tests = {}

        await ZMQUtils.send(self.__backend_socket, AgentJobDone(job_id, (result, text), round(grade, 2), problems, tests, custom, archive, stdout, stderr))

    @abstractmethod
    async def new_job(self, message: BackendNewJob):
        """
        Starts a new job. Most of the time, this function should not call send_job_result directly (as job are intended to be asynchronous). When
        there is a problem starting the job, raise CannotCreateJobException.
        If the job ends immediately, you are free to call send_job_result.
        :param message: message containing all the data needed to start the job
        :return: nothing. If any problems occurs, this method should raise a CannotCreateJobException,
                 which will result in the cancellation of the job.
        """
        pass

    @abstractmethod
    async def kill_job(self, message: BackendKillJob):
        pass
