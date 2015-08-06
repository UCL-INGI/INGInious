# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.

import threading
import os.path
from abc import abstractmethod
import time

from inginious.backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from inginious.backend.job_managers.local import LocalJobManager
from inginious.common.course_factory import create_factories
from inginious.backend.tests.FakeAgents import get_fake_local_agent, FakeRemoteAgent


class TestJobManager(object):
    def __init__(self, job_manager_class=LocalJobManager):
        self.job_manager_init = job_manager_class

    @abstractmethod
    def setUp_job_manager(self):
        pass

    def setUp(self):
        self.course_factory, self.task_factory = create_factories(os.path.join(os.path.dirname(__file__), 'tasks'))
        self.setUp_job_manager()
        self.callback_done = threading.Event()
        self.got_callback_result = None

    def default_callback(self, result):
        self.got_callback_result = result
        self.callback_done.set()

    def wait_for_callback(self, timeout=10):
        self.callback_done.wait(timeout)
        if not self.callback_done.is_set():
            raise Exception("Callback never called")
        return self.got_callback_result

    def tearDown(self):
        self.job_manager.close()


def get_test_port():
    """
    :return: a unique port for this series of tests
    """
    get_test_port.current_port = get_test_port.current_port + 1
    return get_test_port.current_port


get_test_port.current_port = 61000


class TestRemoteJobManager(TestJobManager):
    port = None

    def _get_port(self):
        if not self.port:
            self.port = get_test_port()
        return self.port

    def setUp_job_manager(self):
        self.job_manager = RemoteManualAgentJobManager([{"host": "localhost", "port": self._get_port()}],
                                                       {"default": "ingi/inginious-c-default"},
                                                       os.path.join(os.path.dirname(__file__), 'tasks'),
                                                       self.course_factory,
                                                       self.task_factory,
                                                       self.generate_hook_manager(),
                                                       True)
        self.job_manager.start()

    def generate_hook_manager(self):
        return None


class TestLocalJobManager(TestJobManager):
    def setUp_job_manager(self):
        self.job_manager = LocalJobManager({"default": "inginious-c-default"},
                                           os.path.join(os.path.dirname(__file__), 'tasks'),
                                           self.course_factory,
                                           self.task_factory,
                                           hook_manager=self.generate_hook_manager(),
                                           agent_class=get_fake_local_agent(self.handle_job_func))
        self.job_manager.start()

    def generate_hook_manager(self):
        return None

    @abstractmethod
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        pass


class TestWithFakeRemoteAgent(TestRemoteJobManager):
    def setUp(self):
        self.agent = FakeRemoteAgent(self._get_port(),
                                     self.handle_job_func,
                                     self.update_image_aliases_func,
                                     self.get_task_directory_hashes_func,
                                     self.update_task_directory_func)
        TestJobManager.setUp(self)

        wait = 0
        while self.job_manager.number_agents_available() != 1 and wait < 3:
            time.sleep(30)
            wait += 1
        assert self.job_manager.number_agents_available() == 1

    def tearDown(self):
        self.agent.close()
        TestJobManager.tearDown(self)

    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        return {"result": "success", "grade": 100.0}

    def update_image_aliases_func(self, image_aliases):
        pass

    def get_task_directory_hashes_func(self):
        return {}

    def update_task_directory_func(self, remote_tar_file, to_delete):
        pass


class TestAgentConnection(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        pass

    def test_connection(self):
        assert self.job_manager.number_agents_available() == 1
