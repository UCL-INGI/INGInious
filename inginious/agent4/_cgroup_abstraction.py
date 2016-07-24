# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    Abstractions that provide zeromq-agents that talk with cgroups.
"""

import asyncio
from abc import abstractmethod

from backend4.messages import KWPRegisterContainer, KWPKilledStatus
from ._pipeline import PipelineElement


class KillerWatcher(PipelineElement):
    """
        Abstract classes that implement basic pipelining behavior for TimeoutWatcher and MemoryWatcher
    """

    def __init__(self, context, name):
        super().__init__(context, name)

    async def _handle_message(self, message):
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

"""
    Creates asyncio-compatible version of the watchers from _cgroup_watchers.py

    If cgroup is not available on the current system, use mockups instead, but disables support for timeouts
    and memory limit detection
"""
try:
    import _cgroup_watchers

    class TimeoutWatcher(KillerWatcher):
        def __init__(self, context):
            super().__init__(context, "timeoutwatcher")
            loop = asyncio.get_event_loop()
            self._watcher = _cgroup_watchers.CGroupTimeoutWatcher()
            loop.create_task(loop.run_in_executor(None, self._watcher.run))

        async def _was_killed(self, container_id):
            return "timeout" if self._watcher.container_had_error(container_id) else None

        async def _register_container(self, container_id, max_mem, timeout, hard_timeout):
            self._watcher.add_container_timeout(container_id, timeout, hard_timeout)

    class MemoryWatcher(KillerWatcher):
        def __init__(self, context):
            super().__init__(context, "memorywatcher")
            loop = asyncio.get_event_loop()
            self._watcher = _cgroup_watchers.CGroupMemoryWatcher()
            loop.create_task(loop.run_in_executor(None, self._watcher.run))

        async def _was_killed(self, containerid):
            return "overflow" if self._watcher.container_had_error(containerid) else None

        async def _register_container(self, container_id, max_mem, timeout, hard_timeout):
            self._watcher.add_container_memory_limit(container_id, max_mem)
except:
    class MockupWatcher(KillerWatcher):
        def __init__(self, context, name):
            super().__init__(context, name)

        async def _was_killed(self, container_id):
            return None

        async def _register_container(self, container_id, max_mem, timeout, hard_timeout):
            pass

    class TimeoutWatcher(MockupWatcher):
        def __init__(self, context):
            super().__init__(context, "timeoutwatcher")


    class MemoryWatcher(MockupWatcher):
        def __init__(self, context):
            super().__init__(context, "memorywatcher")
