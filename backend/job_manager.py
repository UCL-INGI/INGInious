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
""" Contains the class JobManager """

import copy
import signal
import threading
import time
import uuid

import rpyc

from backend.hook_manager import HookManager
def _init_manager():
    """ Makes the manager ignore SIGINT """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class JobManager(object):

    """ Manages jobs """

    def __init__(self, agents, hook_manager=None, is_testing=False):
        """
            Starts a job manager.

            Arguments:

            *agents*
                A list of dictionaries containing information about distant backend agents:
                ::

                    {
                        'host': "the host of the agent",
                        'port': "the port on which the agent listens"
                    }

            *hook_manager*
                An instance of HookManager. If no instance is given, a new one will be created.

        """

        self._closed = False
        self._is_testing = is_testing
        self._hook_manager = HookManager() if hook_manager is None else hook_manager
        self._agents = [None for _ in range(0, len(agents))]
        self._agents_thread = [None for _ in range(0, len(agents))]
        self._agents_info = agents
        self._try_agent_connection()

        self._next_agent = 0

        self._running_job_data = {}
        self._running_on_agent = [[] for _ in range(0, len(agents))]

        print "Job Manager initialization done"
        self._hook_manager.call_hook("job_manager_init_done", job_manager=self)

    def _try_agent_connection(self):
        """ Tries to connect to the agents that are not connected yet """
        if self._closed:
            return

        for entry, info in enumerate(self._agents_info):
            if self._agents[entry] is None:
                try:
                    conn = rpyc.connect(info['host'], info['port'], service=self._get_rpyc_server(entry), config={"allow_public_attrs": True, 'allow_pickle': True})
                except:
                    self._agents[entry] = None
                    self._agents_thread[entry] = None
                    print "Cannot connect to agent {}-{}".format(info['host'], info['port'])
                else:
                    self._agents[entry] = conn
                    self._agents_thread[entry] = rpyc.BgServingThread(conn)

        if not self._is_testing:
            threading.Timer(10, self._try_agent_connection).start()

    def _select_agent(self):
        """ Select which agent should handle the next job.
            For now we use a round-robin, but will probably be improved over time.
        """
        available_agents = [i for i, j in enumerate(self._agents) if j is not None]
        if len(available_agents) == 0:
            return None
        chosen_agent = available_agents[self._next_agent % len(available_agents)]
        self._next_agent += 1
        return chosen_agent

    def _execute_job(self, jobid, task, inputdata, debug):
        """ Chooses an agent and executes a job on it """
        agent_id = self._select_agent()
        if agent_id is None:
            self._job_ended(jobid,
                            {'result': 'crash',
                             'text': 'There are not any agent available for grading. Please retry later. If this error persists, please contact the course administrator.'}, None)
            return
        try:
            agent = self._agents[agent_id]
            async_run = rpyc.async(agent.root.new_job)
            result = async_run(str(jobid), str(task.get_course_id()), str(task.get_id()), dict(inputdata), debug, None)
            self._running_on_agent[agent_id].append(jobid)
            result.add_callback(lambda r: self._job_ended(jobid, r.value, agent_id))
        except:
            self._agent_shutdown(agent_id)
            self._execute_job(jobid, task, inputdata, debug)

    def _get_rpyc_server(self, agent_id):
        """ Return a service associated with this JobManager instance """
        on_agent_connection = self._on_agent_connection
        on_agent_disconnection = self._on_agent_disconnection

        class MasterBackendServer(rpyc.Service):

            def on_connect(self):
                on_agent_connection()

            def on_disconnect(self):
                on_agent_disconnection(agent_id)

        return MasterBackendServer

    def _on_agent_connection(self):
        """ Called when a RPyC service start: handles the connection of a distant Agent """
        print "Agent connected"

    def _on_agent_disconnection(self, agent_id):
        """ Called when a RPyC service ends: handles the disconnection of a distant Agent """
        print "Agent disconnected"
        self._agent_shutdown(agent_id)

    def _agent_shutdown(self, agent_id):
        """ Close a connection to an agent (failure/...) """

        # delete jobs that were running on this agent
        map(lambda jid: self._job_ended(jid, {'result': 'crash', 'text': 'Remote agent shutdown'}, agent_id), self._running_on_agent[agent_id])

        try:
            self._agents[agent_id] = None
            self._running_on_agent[agent_id] = []
            self._agents_thread[agent_id].close()
        except:
            pass

    def _job_ended(self, jobid, result, agent_id):
        """ Called when a job is done. results is a dictionary containing the results of the execution of the task on a remote Agent """
        task, callback, base_dict, statinfo = self._running_job_data[jobid]

        # Deletes from data structures
        del self._running_job_data[jobid]
        if agent_id is not None:
            self._running_on_agent[agent_id].remove(jobid)

        # Deepcopy result (to bypass RPyC "reference")
        result = copy.deepcopy(result)

        # Merge the results with the one of the multiple-choice questions
        final_result = self._merge_results(base_dict, result)

        # Call the callback
        # try:
        callback(jobid, task, final_result)
        # except Exception as e:
        #    print "JobManager failed to call the callback function for jobid {}: {}".format(jobid, repr(e))

        self._hook_manager.call_hook("job_ended", jobid=jobid, task=task, statinfo=statinfo, result=final_result)

    def _merge_results(self, origin_dict, emul_result):
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
            final_dict["grade"] = 0
        elif final_dict["grade"] > 200:  # allow bonuses
            final_dict["grade"] = 200
        return final_dict

    def number_agents_available(self):
        """ Returns the number of connected agents """
        return len([entry for entry in self._agents if entry is not None])

    def get_waiting_jobs_count(self):
        """Returns the total number of waiting jobs in the Job Manager"""
        return len(self._running_job_data)

    def new_job_id(self):
        """ Returns a new job id. The job id is unique and should be passed to the new_job function """
        return uuid.uuid4()

    def new_job(self, task, inputdata, callback, launcher_name="Unknown", jobid=None, debug=False):
        """ Add a new job. callback is a function that will be called asynchronously in the job manager's process. """
        if jobid is None:
            jobid = self.new_job_id()

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
        self._running_job_data[jobid] = (task, callback, basedict, statinfo)
        self._hook_manager.call_hook("new_job", jobid=jobid, task=task, statinfo=statinfo, inputdata=inputdata)

        if need_emul:  # Go through the whole process: sent everything to Agent
            self._execute_job(jobid, task, inputdata, debug)
        else:  # If we only have questions that do not need to be "runned", simply directly return the answer
            self._job_ended(jobid, None, None)

        return jobid

    def close(self):
        """ Close all connections to agents """
        self._closed = True
        for i, entry in enumerate(self._agents):
            if entry is not None:
                # Hack a bit BgServingThread to ensure it closes properly
                thread = self._agents_thread[i]
                thread._active = False
                self._agents[i] = None
                self._agents_thread[i] = None
                entry.close()
                thread._thread.join()
                thread._conn = None