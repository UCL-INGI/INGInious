# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    Abstractions that provide zeromq-agents that talk with cgroups.
"""

import asyncio
import logging
from abc import abstractmethod

from inginious.agent._pipeline import PipelineElement
from inginious.common.asyncio_utils import AsyncIteratorWrapper
from inginious.common.messages import KWPRegisterContainer, KWPKilledStatus


class KillerWatcher(PipelineElement):
    """
        Abstract classes that implement basic pipelining behavior for TimeoutWatcher and MemoryWatcher
    """

    def __init__(self, context, name):
        super().__init__(context, name)
        self._logger = logging.getLogger("inginious.agent.docker")

    async def _handle_message(self, message):
        """
        Handles a message. Dispatches it to the right method, then pushes the result in the pipeline.
        """
        try:
            if type(message) == KWPRegisterContainer:
                await self._register_container(message.container_id, message.max_mem, message.timeout, message.timeout_hard)
                return message
            elif type(message) == KWPKilledStatus:
                if message.killed_result is None:
                    killed = await self._was_killed(message.container_id)
                    if killed is not None:
                        return message.killed(killed)
                    else:
                        return message.not_killed()
                else:
                    return message.not_killed()
            else:
                # drop
                pass
        except:
            self._logger.exception("Exception in KillerWatcher._handle_message")

    @abstractmethod
    async def _was_killed(self, container_id):
        """
        :param container_id: the container id to check
        :return: a string with an error code if the container was killed. None if it was not.
        """
        return None

    @abstractmethod
    async def _register_container(self, container_id, max_mem, timeout, hard_timeout):
        """
        Register a container into the watcher
        :param container_id: the container id to register
        """
        pass


class TimeoutWatcher(KillerWatcher):
    def __init__(self, context, docker_interface):
        super().__init__(context, "timeoutwatcher")
        self._loop = asyncio.get_event_loop()
        self.container_had_error = set()
        self.watching = set()
        self.docker_interface = docker_interface

    async def _was_killed(self, container_id):
        if container_id in self.watching:
            self.watching.remove(container_id)
        if container_id in self.container_had_error:
            self.container_had_error.remove(container_id)
            return "timeout"
        return None

    async def _register_container(self, container_id, max_mem, timeout, hard_timeout):
        self.watching.add(container_id)
        self._loop.create_task(self._handle_container_timeout(container_id, timeout))
        self._loop.call_later(hard_timeout, asyncio.ensure_future, self._handle_container_hard_timeout(container_id, hard_timeout))

    async def _handle_container_timeout(self, container_id, timeout):
        """
        Check timeout with docker stats
        :param container_id:
        :param timeout: in seconds (cpu time)
        """
        try:
            docker_stats = self.docker_interface.get_stats(container_id)
            source = AsyncIteratorWrapper(docker_stats)
            nano_timeout = timeout * (10 ** 9)
            async for upd in source:
                if upd is None:
                    await self._kill_it_with_fire(container_id)
                self._logger.debug("%i", upd['cpu_stats']['cpu_usage']['total_usage'])
                if upd['cpu_stats']['cpu_usage']['total_usage'] > nano_timeout:
                    self._logger.info("Killing container %s as it used %i CPU seconds (max was %i)",
                                      container_id, int(upd['cpu_stats']['cpu_usage']['total_usage'] / (10 ** 9)), timeout)
                    await self._kill_it_with_fire(container_id)
                    return
        except:
            self._logger.exception("Exception in _handle_container_timeout")

    async def _handle_container_hard_timeout(self, container_id, hard_timeout):
        """
        Kills a container (should be called with loop.call_later(hard_timeout, ...)) and displays a message on the log
        :param container_id:
        :param hard_timeout:
        :return:
        """
        if container_id in self.watching:
            self._logger.info("Killing container %s as it used its %i wall time seconds",
                              container_id, hard_timeout)
            await self._kill_it_with_fire(container_id)

    async def _kill_it_with_fire(self, container_id):
        """
        Kill a container, with fire.
        """
        if container_id in self.watching:
            self.watching.remove(container_id)
            self.container_had_error.add(container_id)
            try:
                await self._loop.run_in_executor(None, lambda: self.docker_interface.kill_container(container_id))
            except:
                pass #is ok
