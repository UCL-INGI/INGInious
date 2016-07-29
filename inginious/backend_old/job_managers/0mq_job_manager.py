# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from inginious.backend.job_managers.abstract import AbstractJobManager
import zmq

class ZMQJobManager(AbstractJobManager):
    def __init__(self, agents, image_aliases, task_directory, course_factory, task_factory, hook_manager=None, is_testing=False):
        """
            Starts the job manager.

            Arguments:

            :param agents:
                A list of dictionaries containing information about distant inginious.backend agents:
                ::

                    {
                        'location': "the location of the agent, in a zeromq compatible form (ex tcp://myhost:2222)"
                        'ssh_port': "the port on which the interface for accessing the debug ssh server is accessible (not mandatory, can be None)"
                    }

                If a least one ssh_port is absent or None, remote debugging will be deactivated for all agents
            :param task_directory: the task directory
            :param course_factory: a CourseFactory object
            :param task_factory: a TaskFactory object, possibly with specific task files managers attached
            :param image_aliases: a dict of image aliases, like {"default": "ingi/inginious-c-default"}.
            :param hook_manager: An instance of HookManager. If no instance is given(None), a new one will be created.
        """
        super().__init__(image_aliases, hook_manager, is_testing)

        self._context = zmq.Context()

        self._task_directory = task_directory

        # sockets to the agent
        self._agents = [self._context.socket(zmq.REQ) for _ in agents]
        for idx, agent_info in enumerate(agents):
            self._agents[idx].connect(agent_info["location"])
        self._agents_info = agents

        self._course_factory = course_factory
        self._task_factory = task_factory

        self._next_agent = 0
        self._running_on_agent = [[] for _ in range(0, len(agents))]

        self._last_content_in_task_directory = None

        self._timers = {}

        # Is remote debugging activated?
        nb_ok = 0
        message = "ok"

        for info in self._agents_info:
            if info.get('ssh_port') is not None:
                nb_ok += 1
            elif nb_ok != 0:
                nb_ok = -1
                message = "one_error"

        if nb_ok == 0:
            self._remote_debugging_activated = False
            self._logger.info("Remote debugging is deactivated as all agent have no ssh_port defined")
        elif nb_ok == -1:
            self._remote_debugging_activated = False
            self._logger.info("Remote debugging is deactivated as one agent has no ssh_port defined")
        else:
            self._remote_debugging_activated = True

    def get_socket_to_debug_ssh(self, job_id):
        pass

    def kill_job(self, job_id):
        pass

    def close(self):
        pass

    def _get_batch_container_metadata_from_agent(self, container_name):
        pass

    def _execute_batch_job(self, jobid, container_name, inputdata):
        pass

    def is_remote_debug_active(self):
        pass

    def _execute_job(self, jobid, task, inputdata, debug):
        pass

    def start(self):
        pass