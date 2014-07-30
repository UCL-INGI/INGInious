""" Contains the class CallbackManager, used by JobManager. Runs the callbacks. """
import threading


class CallbackManager(threading.Thread):

    """ Runs callback in the job manager's process """

    def __init__(self, input_queue, waiting_job_data, running_job_count, running_job_count_lock):
        threading.Thread.__init__(self)
        self.daemon = True
        self._input_queue = input_queue
        self._waiting_job_data = waiting_job_data
        self._running_job_count = running_job_count
        self._running_job_count_lock = running_job_count_lock

    def run(self):
        while True:
            try:
                docker_instanceid, jobid, result = self._input_queue.get()
            except EOFError:
                return

            print "CallbackManager received result for jobid {}".format(jobid)
            task, callback, base_dict = self._waiting_job_data[jobid]

            final_result = self._merge_emul_result(base_dict, result)

            try:
                callback(jobid, task, final_result)
            except:
                print "CallbackManager failed to call the callback function for jobid {}".format(jobid)

            # Decrement the job counter
            if docker_instanceid is not None:
                self._running_job_count_lock.acquire()
                self._running_job_count[docker_instanceid] = self._running_job_count[docker_instanceid] - 1
                self._running_job_count_lock.release()

    def _merge_emul_result(self, origin_dict, emul_result):
        """ Merge the results of the multiple-choice (and other special problem types) questions with the returned results of the containers """

        # If no docker job was run, returns directly the original response dict.
        if emul_result is None:
            return origin_dict

        # Else merge everything
        if emul_result['result'] not in ["error", "failed", "success", "timeout", "overflow"]:
            emul_result['result'] = "error"

        if emul_result["result"] not in ["error", "timeout", "overflow"]:
            final_dict = emul_result

            final_dict["result"] = "success" if origin_dict["result"] == "success" and final_dict["result"] == "success" else "failed"
            if "text" in final_dict and "text" in origin_dict:
                final_dict["text"] = final_dict["text"] + "\n" + "\n".join(origin_dict["text"])
            elif "text" not in final_dict and "text" in origin_dict:
                final_dict["text"] = "\n".join(origin_dict["text"])

            if "problems" in final_dict and "problems" in origin_dict:
                for pid in origin_dict["problems"]:
                    if pid in final_dict["problems"]:
                        final_dict["problems"][pid] = final_dict["problems"][pid] + "\n" + origin_dict["problems"][pid]
                    else:
                        final_dict["problems"][pid] = origin_dict["problems"][pid]
            elif "problems" not in final_dict and "problems" in origin_dict:
                final_dict["problems"] = origin_dict["problems"]
        elif emul_result["result"] in ["error", "timeout", "overflow"] and "text" in emul_result:
            final_dict = origin_dict.copy()
            final_dict.update({"result": emul_result["result"], "text": emul_result["text"]})
        elif emul_result["result"] == "error":
            final_dict = origin_dict.copy()
            final_dict.update({"result": emul_result["result"], "text": "An unknown internal error occured"})
        elif emul_result["result"] == "timeout":
            final_dict = origin_dict.copy()
            final_dict.update({"result": emul_result["result"], "text": "Your code took too much time to execute"})
        elif emul_result["result"] == "overflow":
            final_dict = origin_dict.copy()
            final_dict.update({"result": emul_result["result"], "text": "Your code took too much memory or disk"})
        return final_dict
