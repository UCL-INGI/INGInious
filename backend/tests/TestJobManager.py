import threading
import os.path

from backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from backend.job_managers.local import LocalJobManager
import common.base
from abc import abstractmethod
from backend.tests.FakeAgents import get_fake_local_agent, FakeRemoteAgent

class TestJobManager(object):
    def __init__(self, job_manager_class=LocalJobManager):
        self.job_manager_init = job_manager_class

    @abstractmethod
    def setUp_job_manager(self):
        pass

    def setUp(self):
        common.base.init_common_lib(os.path.join(os.path.dirname(__file__), 'tasks'),
                                    [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"],
                                    1024 * 1024)
        self.setUp_job_manager()
        self.callback_done = threading.Event()
        self.got_callback_result = None

    def default_callback(self, _, _2, result):
        self.got_callback_result = result
        self.callback_done.set()

    def wait_for_callback(self, timeout=10):
        self.callback_done.wait(timeout)
        if not self.callback_done.is_set():
            raise Exception("Callback never called")
        return self.got_callback_result

    def tearDown(self):
        self.job_manager.close()


class TestRemoteJobManager(TestJobManager):
    def setUp_job_manager(self):
        self.job_manager = RemoteManualAgentJobManager([{"host": "localhost", "port": 5002}], {"default": "ingi/inginious-c-default"})

class TestLocalJobManager(TestJobManager):
    def setUp_job_manager(self):
        self.job_manager = LocalJobManager({"default": "inginious-c-default"}, agent_class=get_fake_local_agent(self.handle_job_func))

    @abstractmethod
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        pass

class TestWithFakeRemoteAgent(TestRemoteJobManager):
    def setUp(self):
        self.agent = FakeRemoteAgent(self.handle_job_func)
        TestJobManager.setUp(self)

    @abstractmethod
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        pass

class TestAgentConnection(TestWithFakeRemoteAgent):
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        pass

    def test_connection(self):
        assert self.job_manager.number_agents_available() == 1