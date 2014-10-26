# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" Contains the class CallbackManager, used by JobManager. Runs the callbacks. """
import threading
from common.parsable_text import ParsableText


class CallbackManager(threading.Thread):

    """ Runs callback in the job manager's process and deletes the container """

    def __init__(self, input_queue, docker_instances_config, waiting_job_data, hook_manager):
        threading.Thread.__init__(self)
        self.daemon = True
        self._input_queue = input_queue
        self._waiting_job_data = waiting_job_data
        self._docker_instances_config = docker_instances_config
        self._hook_manager = hook_manager

    def run(self):
        while True:
            try:
                jobid, result = self._input_queue.get()
            except EOFError:
                return

            task, callback, base_dict, statinfo = self._waiting_job_data[jobid]
            del self._waiting_job_data[jobid]

            final_result = self._parse_text(task, self._merge_emul_result(base_dict, result))

            # Call the callback
            try:
                callback(jobid, task, final_result)
            except Exception as e:
                print "CallbackManager failed to call the callback function for jobid {}: {}".format(jobid, repr(e))

            self._hook_manager.call_hook("job_ended", jobid=jobid, task=task, statinfo=statinfo, result=final_result)

    def _parse_text(self, task, final_dict):
        """ Parses text """
        if "text" in final_dict:
            final_dict["text"] = ParsableText(final_dict["text"], task.get_response_type()).parse()
        if "problems" in final_dict:
            for problem in final_dict["problems"]:
                final_dict["problems"][problem] = ParsableText(final_dict["problems"][problem], task.get_response_type()).parse()
        return final_dict

    def _merge_emul_result(self, origin_dict, emul_result):
        """ Merge the results of the multiple-choice (and other special problem types) questions with the returned results of the containers """

        # If no docker job was run, returns directly the original response dict, but without lists
        if emul_result is None:
            if "text" in origin_dict and isinstance(origin_dict["text"], list):
                origin_dict["text"] = "\n".join(origin_dict["text"])
            if "problems" in origin_dict:
                for problem in origin_dict["problems"]:
                    if isinstance(origin_dict["problems"][problem], list):
                        origin_dict["problems"][problem] = "\n".join(origin_dict["problems"][problem])
            return origin_dict

        # Include stderr and stdout (for debug)
        if "stderr" in emul_result:
            origin_dict["stderr"] = emul_result["stderr"]
        if "stdout" in emul_result:
            origin_dict["stdout"] = emul_result["stdout"]

        # Else merge everything
        if emul_result['result'] not in ["error", "failed", "success", "timeout", "overflow", "crash"]:
            emul_result['result'] = "error"

        if emul_result["result"] not in ["error", "timeout", "overflow", "crash"]:
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
        elif emul_result["result"] in ["error", "timeout", "overflow", "crash"] and "text" in emul_result:
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
        elif emul_result["result"] == "crash":
            final_dict = origin_dict.copy()
            final_dict.update({"result": emul_result["result"], "text": "There was an internal error while running the tests"})
        return final_dict
