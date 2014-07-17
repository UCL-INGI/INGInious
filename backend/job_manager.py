""" Contain the abstract class JobManager """

from abc import ABCMeta, abstractmethod
import json
import threading

from common.parsableText import ParsableText


class JobManager (threading.Thread):

    """ Abstract thread class that runs the jobs that are in the queue """
    __metaclass__ = ABCMeta

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Retrieves the task from the queue
            jobid, task, inputdata, callback = self.queue.get_next_job()

            # Base dictonnary with output
            basedict = {"task": task, "input": inputdata}

            # Check task answer that do not need emulation
            first_result, need_emul, first_text, first_problems, multiple_choice_error_count = task.check_answer(inputdata)
            final_dict = basedict.copy()
            final_dict.update({"result": ("success" if first_result else "failed")})
            if first_text is not None:
                final_dict["text"] = first_text
            if first_problems:
                final_dict["problems"] = first_problems
            if multiple_choice_error_count != 0:
                final_dict["text"].append("You have {} errors in the multiple choice questions".format(multiple_choice_error_count))

            # Launch the emulation
            if need_emul:
                try:
                    emul_result = self.run_job(jobid, task, {"limits": task.get_limits(), "input": inputdata})
                    print json.dumps(emul_result, sort_keys=True, indent=4, separators=(',', ': '))
                except Exception:
                    emul_result = {"result": "error", "text": "The grader did not gave any output. This can be because you used too much memory."}

                if final_dict['result'] not in ["error", "failed", "success", "timeout", "overflow"]:
                    final_dict['result'] = "error"

                if emul_result["result"] not in ["error", "timeout", "overflow"]:
                    # Merge results
                    no_vm_dict = final_dict
                    final_dict = emul_result

                    final_dict["result"] = "success" if no_vm_dict["result"] == "success" and final_dict["result"] == "success" else "failed"
                    if "text" in final_dict and "text" in no_vm_dict:
                        final_dict["text"] = final_dict["text"] + "\n" + "\n".join(no_vm_dict["text"])
                    elif "text" not in final_dict and "text" in no_vm_dict:
                        final_dict["text"] = "\n".join(no_vm_dict["text"])

                    if "problems" in final_dict and "problems" in no_vm_dict:
                        for pid in no_vm_dict["problems"]:
                            if pid in final_dict["problems"]:
                                final_dict["problems"][pid] = final_dict["problems"][pid] + "\n" + no_vm_dict["problems"][pid]
                            else:
                                final_dict["problems"][pid] = no_vm_dict["problems"][pid]
                    elif "problems" not in final_dict and "problems" in no_vm_dict:
                        final_dict["problems"] = no_vm_dict["problems"]
                elif emul_result["result"] in ["error", "timeout", "overflow"] and "text" in emul_result:
                    final_dict = basedict.copy()
                    final_dict.update({"result": emul_result["result"], "text": emul_result["text"]})
                elif emul_result["result"] == "error":
                    final_dict = basedict.copy()
                    final_dict.update({"result": emul_result["result"], "text": "An unknown internal error occured"})
                elif emul_result["result"] == "timeout":
                    final_dict = basedict.copy()
                    final_dict.update({"result": emul_result["result"], "text": "Your code took too much time to execute"})
                elif emul_result["result"] == "overflow":
                    final_dict = basedict.copy()
                    final_dict.update({"result": emul_result["result"], "text": "Your code took too much memory or disk"})
            else:
                final_dict["text"] = "\n".join(final_dict["text"])

            # Parse returned content
            if "text" in final_dict:
                final_dict["text"] = ParsableText(final_dict["text"], task.get_response_type()).parse()
            if "problems" in final_dict:
                for pid in final_dict["problems"]:
                    final_dict["problems"][pid] = ParsableText(final_dict["problems"][pid], task.get_response_type()).parse()

            self.queue.set_result(jobid, final_dict)
            if callback is not None:
                callback(jobid, final_dict)

    @abstractmethod
    def run_job(self, jobid, task, inputdata):
        """ Run a new job """
        pass
