# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    Utilities for asyncio
"""

import asyncio


class AsyncIteratorWrapper:
    """
        A wrapper that converts old-style-generators to async generators using run_in_executor
    """

    def __init__(self, obj):
        self._it = obj
        self._loop = asyncio.get_event_loop()

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = await self._loop.run_in_executor(None, lambda: next(self._it))
        except StopIteration:
            raise StopAsyncIteration
        return value