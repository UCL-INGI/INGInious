# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import asyncio
import logging

import zmq

from inginious.common.course_factory import CourseFactory, create_factories
from inginious.common.message_meta import ZMQUtils
from inginious.common.messages import BackendNewJob, BackendKillJob, BackendNewBatchJob, AgentBatchJobDone, AgentHello, AgentJobDone


class MCQAgent(object):
    def __init__(self, context, backend_addr, task_directory):
        """
        :param context: ZeroMQ context for this process
        :param backend_addr: address of the backend (for example, "tcp://127.0.0.1:2222")
        :param course_factory: course factory
        :param task_factory: task factory
        """
        self._logger = logging.getLogger("inginious.agent.mcq")

        self._backend_addr = backend_addr
        self._context = context
        self._loop = asyncio.get_event_loop()

        # Create a course factory
        course_factory, _ = create_factories(task_directory)
        self.course_factory = course_factory

        # Sockets
        self._backend_socket = self._context.socket(zmq.DEALER)

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

    async def handle_new_batch_job(self, msg: BackendNewBatchJob):
        """ Handle a batch job message. Should not be called. Ever. """
        ZMQUtils.send(self._backend_socket, AgentBatchJobDone(msg.job_id, -1, "This agent cannot run batch jobs", "This agent cannot run batch "
                                                                                                                  "jobs", None))
        self._logger.error("BackendNewBatchJob received, which does not make sense for a MCQ agent")

    async def handle_kill_job(self, msg: BackendKillJob):
        """ Kill a running job. But there are none, so we just ignore the message """
        pass

    async def handle_new_job(self, msg: BackendNewJob):
        """ Handles a new job. Returns immediately the result of the MCQ """
        try:
            task = self.course_factory.get_task(msg.course_id, msg.task_id)
        except:
            await ZMQUtils.send(self._backend_socket, AgentJobDone(msg.job_id, ("crash", "Task is not available on this agent"), 0.0, {}, {}, {},
                                                                   None, "", ""))
            self._logger.error("Task %s/%s not available on this agent", msg.course_id, msg.task_id)
            return

        result, need_emul, text, problems, error_count = task.check_answer(msg.inputdata)
        if need_emul:
            await ZMQUtils.send(self._backend_socket, AgentJobDone(msg.job_id, ("crash", "Task wrongly configured as a MCQ"), 0.0, {}, {}, {}, None, "", ""))
            self._logger.warning("Task %s/%s is not a pure MCQ but has env=MCQ", msg.course_id, msg.task_id)
            return

        if error_count != 0:
            text.append("You have %i errors in the multiple choice questions" % error_count)

        nb_subproblems = len(task.get_problems())
        grade = 100.0 * float(nb_subproblems - error_count) / float(nb_subproblems)

        await ZMQUtils.send(self._backend_socket, AgentJobDone(msg.job_id,
                                                               (("success" if result else "failed"), "\n".join(text)),
                                                               grade, problems, {}, {}, None, "", ""))

    async def run_dealer(self):
        """ Run the agent """
        self._logger.info("Agent started")
        self._backend_socket.connect(self._backend_addr)

        # Tell the backend we are up
        self._logger.info("Saying hello to the backend")
        await ZMQUtils.send(self._backend_socket, AgentHello(1, {"mcq": {"id": "mcq", "created": 0}}, {}))

        # And then run the agent
        try:
            while True:
                message = await ZMQUtils.recv(self._backend_socket)
                await self.handle_backend_message(message)
        except asyncio.CancelledError:
            return
        except KeyboardInterrupt:
            return
