# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    Utilities for asyncio
"""

import asyncio
import threading


class AsyncIteratorWrapper(object):
    """ A wrapper that converts old-style-generators to async generators using run_in_executor """
    def __init__(self, obj):
        self._it = obj
        self._loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue()
        self._last_item = object()
        self._thread = threading.Thread(target=self._unroll)
        self._thread.daemon = True
        self._thread.start()

    async def __aiter__(self):
        return self

    async def __anext__(self):
        value = await self._queue.get()
        if value == self._last_item:
            raise StopAsyncIteration
        return value

    async def _add_to_queue(self, o):
        await self._queue.put(o)

    def _unroll(self):
        try:
            for i in self._it:
                self._loop.call_soon_threadsafe(asyncio.ensure_future, self._add_to_queue(i))
        except Exception:
            pass
        self._loop.call_soon_threadsafe(asyncio.ensure_future, self._add_to_queue(self._last_item))
