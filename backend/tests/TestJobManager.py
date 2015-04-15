from backend.job_manager import JobManager
import threading
import os.path
import common.base

class TestJobManager(object):
    def setUp(self):
        common.base.init_common_lib(os.path.join(os.path.dirname(__file__), 'tasks'),
                                    [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"],
                                    1024 * 1024)

        self.job_manager = JobManager([{"host": "localhost", "port": 5002}])
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