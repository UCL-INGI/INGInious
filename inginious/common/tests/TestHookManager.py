# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from inginious.common.hook_manager import HookManager


class TestHookManager(object):
    def make_exception(self):
        raise Exception()

    def test_exception(self):
        """ Hook Manager should silently ignore hooks that make exceptions"""
        hook_manager = HookManager()
        hook_manager.add_hook("test", self.make_exception)
        hook_manager.add_hook("test", lambda: 42)
        retval = hook_manager.call_hook("test")
        assert retval == [42]

    def test_multple(self):
        hook_manager = HookManager()
        hook_manager.add_hook("test", lambda: 43)
        hook_manager.add_hook("test", lambda: 42)
        hook_manager.add_hook("test", lambda: 44)
        retval = hook_manager.call_hook("test")
        assert set(retval) == {42, 43, 44}
