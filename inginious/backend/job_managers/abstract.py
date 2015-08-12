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
""" Contains the class AbstractJobManager, which is the basic implementation of the inginious.backend """

import time
import uuid
from abc import abstractmethod

from inginious.common.hook_manager import HookManager

def _callable_once(func):
    """ Returns a function that is only callable once; any other call will do nothing """
    def once(*args, **kwargs):
        if not once.called:
            once.called = True
            return func(*args, **kwargs)
    once.called = False
    return once

class AbstractJobManager(object):
    """ Manages jobs """

    def __init__(self, image_aliases, hook_manager=None, is_testing=False):
        """
        Creates a job manager.
        :param image_aliases: a dict of image aliases, like {"default": "ingi/inginious-c-default"}.
        :param hook_manager: An instance of HookManager. If no instance is given(None), a new one will be created.
        """

        self._closed = False
        self._is_testing = is_testing
        self._image_aliases = image_aliases
        self._hook_manager = HookManager() if hook_manager is None else hook_manager
        self._running_job_data = {}
        self._running_batch_job_data = {}
        self._batch_container_args = {}
        self._active_ssh_debug_servers = {}

        print "Job Manager initialization done"
        self._hook_manager.call_hook("job_manager_init_done", job_manager=self)

    @abstractmethod
    def start(self):
        """ Starts the Job Manager. Should be done after a complete initialisation of the hook manager. """
        pass

    @abstractmethod
    def _execute_job(self, jobid, task, inputdata, debug):
        """ Executes a job in a Docker container, then calls self._job_ended with the result.
        :param jobid: The job id
        :param task:  The Task instance linked to the job to run
        :param inputdata: Input given by the student
        :param debug: Boolean indicating if the job should be run with the debug status
        """
        pass

    @abstractmethod
    def _execute_batch_job(self, jobid, container_name, inputdata):
        """ Executes a batch job in the specified Docker container, then calls self._batch_job_ended with the result.
        :param jobid: The job id
        :param container_name:  The name of the container to run
        :param inputdata: tgz file
        """
        pass

    @abstractmethod
    def _get_batch_container_metadata_from_agent(self, container_name):
        """
            Returns the arguments needed by a particular batch container.
            :returns: a dict in the form
                ("container title",
                 "container description in restructuredtext",
                 {"key":
                    {
                     "type:" "file", #or "text",
                     "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                     "name": "name of the field", #not mandatory in file, default "key"
                     "description": "a short description of what this field is used for", #not mandatory, default ""
                     "custom_key1": "custom_value1",
                     ...
                    }
                 }
                )
        """
        pass

    def get_batch_container_metadata(self, container_name):
        """
            Returns the arguments needed by a particular batch container (cached version)
            :returns: a dict in the form
                ("container title",
                 "container description in restructuredtext",
                 {"key":
                    {
                     "type:" "file", #or "text",
                     "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                     "name": "name of the field", #not mandatory in file, default "key"
                     "description": "a short description of what this field is used for", #not mandatory, default ""
                     "custom_key1": "custom_value1",
                     ...
                    }
                 }
                )
        """
        if container_name not in self._batch_container_args:
            ret = self._get_batch_container_metadata_from_agent(container_name)
            if ret == (None, None, None):
                return ret
            self._batch_container_args[container_name] = ret
        return self._batch_container_args[container_name]

    @abstractmethod
    def close(self):
        """ Close the Job Manager """
        pass

    def _job_ended(self, jobid, result):
        """ Called when a job is done. results is a dictionary containing the results of the execution of the task on a remote Agent """
        task, callback, ssh_callback, base_dict, statinfo = self._running_job_data[jobid]

        # Ensure ssh_callback is called at least once
        try:
            ssh_callback(jobid, "")  # NB: origin ssh_callback was wrapped with _callable_once
        except:
            pass
        self._close_distant_debug_ssh(jobid)

        # Deletes from data structures
        del self._running_job_data[jobid]

        # Merge the results with the one of the multiple-choice questions
        final_result = self._merge_results(base_dict, result)

        # Call the callback
        try:
            callback(final_result)
        except Exception as e:
            print "JobManager failed to call the callback function for jobid {}: {}".format(jobid, repr(e))

        self._hook_manager.call_hook("job_ended", jobid=jobid, task=task, statinfo=statinfo, result=final_result)

    def _batch_job_ended(self, jobid, result):
        """ Called when a batch job is done. results is a dictionnary, containing:

            - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
                if everything went well. (where file is a tgz file containing the content of the /output folder from the container)
            - {"retval":"...", "stdout": "...", "stderr":"..."}
                if the container crashed (retval is an int != 0) (can also contain file, but not mandatory)
            - {"retval":-1, "stderr": "the error message"}
                if the container failed to start
        """
        container_name, callback, _, statinfo = self._running_batch_job_data[jobid]

        # Deletes from data structures
        del self._running_batch_job_data[jobid]

        # Call the callback
        try:
            callback(result)
        except Exception as e:
            print "JobManager failed to call the callback function for jobid {}: {}".format(jobid, repr(e))

        self._hook_manager.call_hook("batch_job_ended", jobid=jobid, statinfo=statinfo, result=result)

    @classmethod
    def _merge_results(cls, origin_dict, emul_result):
        """ Merge the results of the multiple-choice (and other special problem types) questions with the returned results of the containers """

        # If no docker job was run, returns directly the original response dict, but without lists
        if emul_result is None:
            if "text" in origin_dict and isinstance(origin_dict["text"], list):
                origin_dict["text"] = "\n".join(origin_dict["text"])
            if "problems" in origin_dict:
                for problem in origin_dict["problems"]:
                    if isinstance(origin_dict["problems"][problem], list):
                        origin_dict["problems"][problem] = "\n".join(origin_dict["problems"][problem])
            final_dict = origin_dict
        else:
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
            else:
                final_dict = origin_dict.copy()
                error_messages = {
                    "error": "An unknown internal error occured",
                    "timeout": "Your code took too much time to execute",
                    "overflow": "Your code took too much memory or disk"
                }
                other_message = "There was an internal error while running the tests"
                final_dict.update({"result": emul_result["result"], "text": error_messages.get(emul_result["result"], other_message)})

        # Verify that the grade is present
        if final_dict["result"] in ["success", "failed"]:
            if "grade" not in final_dict:
                final_dict["grade"] = 100.0 if final_dict["result"] == "success" else 0.0
        else:
            final_dict["grade"] = 0.0

        try:
            final_dict["grade"] = float(final_dict["grade"])
        except:
            final_dict["grade"] = 0.0

        if final_dict["grade"] < 0:
            final_dict["grade"] = 0.0
        elif final_dict["grade"] > 200:  # allow bonuses
            final_dict["grade"] = 200.0

        return final_dict

    def get_waiting_jobs_count(self):
        """Returns the total number of waiting jobs in the Job Manager"""
        return len(self._running_job_data)

    def get_waiting_batch_jobs_count(self):
        """Returns the total number of waiting jobs in the Job Manager"""
        return len(self._running_batch_job_data)

    def _new_job_id(self):
        """ Returns a new job id. The job id is unique and should be passed to the new_job function """
        return str(uuid.uuid4())

    def new_job(self, task, inputdata, callback, launcher_name="Unknown", debug=False, ssh_callback=None):
        """ Add a new job. callback is
        :type task: Task
        :param inputdata: input from the student
        :type inputdata: Storage or dict
        :param callback: a function that will be called asynchronously in the job manager's process, with the results
        :type callback: __builtin__.function or __builtin__.instancemethod
        :param launcher_name: for informational use
        :type launcher_name: str
        :param debug: Either True(outputs more info), False(default), or "ssh" (starts a remote ssh server. ssh_callback needs to be defined)
        :type debug: bool or string
        :param ssh_callback: a callback function that will be called with (conn_id, ssh_key), the needed credentials to connect to the remote ssh
            server
        :type ssh_callback: __builtin__.function or __builtin__.instancemethod or None
        :return: the new job id
        """
        """  """
        jobid = self._new_job_id()

        # Verify correctness of debug/ssh_callback
        if debug == "ssh" and ssh_callback is None:
            raise Exception("ssh_callback is None but debug == 'ssh'")
        if debug == "ssh" and not self.is_remote_debug_active():
            raise Exception("Remote debugging is not activated")
        if ssh_callback is None:
            ssh_callback = lambda x, y: None

        # Base dictionary with output
        basedict = {"task": task, "input": inputdata}

        # Check task answers that do not need that we launch a container
        first_result, need_emul, first_text, first_problems, multiple_choice_error_count = task.check_answer(inputdata)
        basedict.update({"result": ("success" if first_result else "failed")})
        if first_text is not None:
            basedict["text"] = first_text
        if first_problems:
            basedict["problems"] = first_problems
        if multiple_choice_error_count != 0:
            basedict["text"].append("You have {} errors in the multiple choice questions".format(multiple_choice_error_count))

        # Compute some informations that will be useful for statistics
        statinfo = {"launched": time.time(), "launcher_name": launcher_name}
        self._running_job_data[jobid] = (task, callback, _callable_once(ssh_callback), basedict, statinfo)
        self._hook_manager.call_hook("new_job", jobid=jobid, task=task, statinfo=statinfo, inputdata=inputdata)

        if need_emul:  # Go through the whole process: send everything to Agent
            self._execute_job(jobid, task, inputdata, debug)
        else:  # If we only have questions that do not need to be "runned", simply directly return the answer
            self._job_ended(jobid, None)

        return jobid

    def new_batch_job(self, container_name, inputdata, callback, launcher_name="Unknown"):
        """ Add a new batch job. callback is a function that will be called asynchronously in the job manager's process.
            inputdata is a dict containing all the keys of get_batch_container_metadata(container_name)[2].
            The values associated are file-like objects for "file" types and  strings for "text" types.
        """
        jobid = self._new_job_id()

        # Verify inputdata
        batch_args = self.get_batch_container_metadata(container_name)[2]
        if set(inputdata.keys()) != set(batch_args.keys()):
            raise Exception("Invalid keys for inputdata")
        for key in batch_args:
            if batch_args[key]["type"] == "text" and not isinstance(inputdata[key], basestring):
                raise Exception("Invalid value for inputdata: the value for key {} should be a string".format(key))
            elif batch_args[key]["type"] == "file" and isinstance(inputdata[key], basestring):
                raise Exception("Invalid value for inputdata: the value for key {} should be a file object".format(key))

        # Compute some informations that will be useful for statistics
        statinfo = {"launched": time.time(), "launcher_name": launcher_name}
        self._running_batch_job_data[jobid] = (container_name, callback, inputdata, statinfo)

        self._hook_manager.call_hook("new_batch_job", jobid=jobid, statinfo=statinfo, inputdata=inputdata)

        self._execute_batch_job(jobid, container_name, inputdata)

        return jobid

    def _handle_ssh_callback(self, job_id, distant_conn_id, ssh_key):
        """ Handles the callback, coming from the agent, giving the conn_id and the ssh_key needed to connect to the debug ssh server"""
        data = self._running_job_data.get(job_id)
        if data is None: #prevent race conditions...
            return
        task, callback, ssh_callback, base_dict, statinfo = data

        self._active_ssh_debug_servers[job_id] = distant_conn_id

        try:
            ssh_callback(job_id, ssh_key)
        except Exception as e:
            print ("Cannot execute ssh callback for job id %s: %s" % (job_id, str(e)))

    def _get_distant_conn_id_for_job(self, job_id):
        """ Get the distant connection id for a job_id. Returns None if the conn_id is expired or not valid. """
        return self._active_ssh_debug_servers.get(job_id, None)

    def _close_distant_debug_ssh(self, job_id):
        """ Remove the possibility to get a socket to a possible debug ssh server associated with this job_id """
        try:  # better ask forgiveness (and prevent race conditions ;-) )
            del self._active_ssh_debug_servers[job_id]
        except:
            pass

    @abstractmethod
    def is_remote_debug_active(self):
        """
        :return: True if remote container debugging via SSH is activated, False else.
        """
        return False

    @abstractmethod
    def get_socket_to_debug_ssh(self, job_id):
        """ Get a socket to the remote ssh server identified by the job_id. Returns None if the conn_id is expired or not valid. """
        return None