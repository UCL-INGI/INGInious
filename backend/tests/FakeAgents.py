import rpyc
from rpyc.utils.server import OneShotServer
import threading
import copy

def get_fake_local_agent(handle_job_func):
    class FakeLocalAgent(object):
        """ A fake agent used for tests of the local interface"""
        def __init__(self, _, _2):
            self.handle_job_func = handle_job_func

        def new_job(self, job_id, course_id, task_id, inputdata, debug, callback_status, final_callback):
            t = threading.Thread(target=lambda: self._handle_job_threaded(job_id, course_id, task_id, inputdata, debug, callback_status, final_callback))
            t.daemon = True
            t.start()

        def _handle_job_threaded(self, job_id, course_id, task_id, inputdata, debug, callback_status, final_callback):
            try:
                result = self.handle_job_func(job_id, course_id, task_id, inputdata, debug, callback_status)
                final_callback(result)
            except:
                final_callback({"result": "crash"})
    return FakeLocalAgent

class FakeRemoteAgent(threading.Thread):
    """ A fake agent used for tests of the RPyC interface """
    def __init__(self, port, handle_job_func,
                 update_image_aliases_func=(lambda aliases: ""),
                 get_task_directory_hashes_func=(lambda: []),
                 update_task_directory_func=(lambda remote_tar_file, to_delete: "")):
        threading.Thread.__init__(self)
        self.port = port
        self.handle_job_func = handle_job_func
        self.update_image_aliases_func = update_image_aliases_func
        self.get_task_directory_hashes_func = get_task_directory_hashes_func
        self.update_task_directory_func = update_task_directory_func
        self.start()

    def run(self):
        try:
            self._backend_server = OneShotServer(self._get_agent_backend_service(), port=self.port,
                                                 protocol_config={"allow_public_attrs": True, 'allow_pickle': True})
            self._backend_server.start()
        except EOFError:
            pass

    def close(self):
        self._backend_server.close()

    def _get_agent_backend_service(self):
        """ Returns a RPyC service associated with this Agent """
        handle_job = self.handle_job_func
        update_image_aliases_func = self.update_image_aliases_func
        get_task_directory_hashes_func = self.get_task_directory_hashes_func
        update_task_directory_func = self.update_task_directory_func

        class AgentService(rpyc.Service):
            def exposed_update_image_aliases(self, image_aliases):
                update_image_aliases_func(image_aliases)

            def exposed_get_task_directory_hashes(self):
                return get_task_directory_hashes_func()

            def exposed_update_task_directory(self, remote_tar_file, to_delete):
                update_task_directory_func(remote_tar_file.read(), copy.deepcopy(to_delete))

            def exposed_new_job(self, job_id, course_id, task_id, inputdata, debug, callback_status):
                """ Creates, executes and returns the results of a new job """
                return handle_job(job_id, course_id, task_id, inputdata, debug, callback_status)

        return AgentService