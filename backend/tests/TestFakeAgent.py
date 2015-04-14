import rpyc
from rpyc.utils.server import OneShotServer
from abc import abstractmethod
from backend.job_manager import JobManager
import threading

class FakeAgent(threading.Thread):
    """ A fake agent used for tests """
    def __init__(self, handle_job_func):
        threading.Thread.__init__(self)
        self.handle_job_func = handle_job_func
        self.start()

    def run(self):
        try:
            self._backend_server = OneShotServer(self._get_agent_backend_service(), port=5002,
                protocol_config={"allow_public_attrs": True, 'allow_pickle': True})
            self._backend_server.start()
        except EOFError:
            pass

    def _get_agent_backend_service(self):
        """ Returns a RPyC service associated with this Agent """
        handle_job = self.handle_job_func
        class AgentService(rpyc.Service):
            def exposed_new_job(self, job_id, course_id, task_id, inputdata, debug, callback_status):
                """ Creates, executes and returns the results of a new job """
                return handle_job(job_id, course_id, task_id, inputdata, debug, callback_status)

        return AgentService

class TestWithFakeAgent(object):
    def setUp(self):
        self.agent = FakeAgent(self.handle_job_func)
        self.job_manager = JobManager([{"host": "localhost", "port": 5002}])
        self.callback_done = threading.Event()
        assert self.job_manager.number_agents_available() == 1

    @abstractmethod
    def handle_job_func(self, job_id, course_id, task_id, inputdata, debug, callback_status):
        pass

    def default_callback(self, _, _2, _3):
        self.callback_done.set()

    def wait_for_callback(self, timeout=10):
        self.callback_done.wait(timeout)
        if not self.callback_done.is_set():
            raise Exception("Callback never called")

    def tearDown(self):
        self.job_manager.close()