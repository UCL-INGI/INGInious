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
""" A JobManager that can interact with distant agents, via RPyC """

import threading

import rpyc

from backend.job_managers.abstract import AbstractJobManager


class RemoteAgentJobManager(AbstractJobManager):
    """ A Job Manager that handles connections with distant Agents using RPyC """
    def __init__(self, agents, hook_manager=None, is_testing=False):
        """
            Starts the job manager.

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

        AbstractJobManager.__init__(self, hook_manager, is_testing)
        self._agents = [None for _ in range(0, len(agents))]
        self._agents_thread = [None for _ in range(0, len(agents))]
        self._agents_info = agents
        self._try_agent_connection()

        self._next_agent = 0
        self._running_on_agent = [[] for _ in range(0, len(agents))]

    def _try_agent_connection(self):
        """ Tries to connect to the agents that are not connected yet """
        if self._closed:
            return

        for entry, info in enumerate(self._agents_info):
            if self._agents[entry] is None:
                try:
                    conn = rpyc.connect(info['host'], info['port'], service=self._get_rpyc_server(entry),
                                        config={"allow_public_attrs": True, 'allow_pickle': True})
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
                             'text': 'There are not any agent available for grading. Please retry later. If this error persists, please contact the course administrator.'},
                            None)
            return
        try:
            agent = self._agents[agent_id]
            async_run = rpyc.async(agent.root.new_job)
            result = async_run(str(jobid), str(task.get_course_id()), str(task.get_id()), dict(inputdata), debug, None)
            self._running_on_agent[agent_id].append(jobid)
            result.add_callback(lambda r: self._execute_job_callback(jobid, r, agent_id))
        except:
            self._agent_shutdown(agent_id)
            self._execute_job(jobid, task, inputdata, debug)

    def _job_ended(self, jobid, result, agent_id=None):
        if agent_id is not None:
            self._running_on_agent[agent_id].remove(jobid)
        AbstractJobManager._job_ended(self, jobid, result)

    def _execute_job_callback(self, jobid, callback_return_val, agent_id):
        """ Called when an agent is done with a job or raised an exception """
        if callback_return_val.error:
            print "Agent {} made an exception while running jobid {}".format(agent_id, jobid)
            self._job_ended(jobid, {"result": "crash"}, agent_id)
        else:
            self._job_ended(jobid, callback_return_val.value, agent_id)

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

    def number_agents_available(self):
        """ Returns the number of connected agents """
        return len([entry for entry in self._agents if entry is not None])

    def close(self):
        """ Close the Job Manager """
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