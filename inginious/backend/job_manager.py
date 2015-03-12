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
""" Contains the class JobManager """
import multiprocessing.managers
import os
import signal
import time
import uuid

from inginious.backend._callback_manager import CallbackManager
from inginious.backend._message_types import RUN_JOB, CLOSE
import inginious.backend._pool_manager
from inginious.backend.hook_manager import HookManager


def _init_manager():
    """ Makes the manager ignore SIGINT """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class JobManager(object):

    """ Manages jobs """

    def __init__(self, docker_instances, containers_names, tasks_directory, callback_manager_count=1, slow_pool_size=None, fast_pool_size=None, containers_hard=[], hook_manager=None):
        """
            Starts a job manager.

            Arguments:

            *docker_instances*
                A list of dictionaries containing information about a distant docker daemon:
                ::

                    {
                        server_url: "the url to the docker daemon. May be a UNIX socket. Mandatory",
                        max_concurrent_jobs: 100
                    }

            *containers_names*
                A dict containing, as key, a simple name for each container image, and as value the urls to get the docker container images.

            *tasks_directory*
                The local directory path containing the courses and the tasks

            *slow_pool_size* and *fast_pool_size*
                Size of the process pool which runs respectively actions that are slow or fast. Default: number of processors
                Slow actions includes:

                -    waiting for containers

                -    deleting containers

                -    building container images

                Fast actions are:

                -    creating and launching a container

                -    retrieving results from a container

            *callback_manager_count*
                Number of thread to launch to handle the callbacks

            *hook_manager*
                An instance of HookManager. If no instance is given, a new one will be created.

            A job manager launches in fact a process called a pool manager.

            A pool manager runs two pools of processes, one for actions that are slow, the other for fast actions.

            The job manager also launch a number of thread to handle the callbacks (the number is given by callback_manager_count)
        """
        self._containers_names = containers_names
        self._tasks_directory = tasks_directory
        self._docker_config = docker_instances

        self._hook_manager = HookManager() if hook_manager is None else hook_manager

        self._memory_manager = multiprocessing.managers.SyncManager()
        self._memory_manager.start(_init_manager)

        self._operations_queue = self._memory_manager.Queue()
        self._done_queue = self._memory_manager.Queue()

        self._running_job_data = {}

        # Correct the size of the slow pool size, which will contain all waiters
        if (multiprocessing.cpu_count() if slow_pool_size is None else slow_pool_size) < len(self._docker_config) + 1:
            slow_pool_size = len(self._docker_config) + 1

        # Start the pool manager
        self._pool_manager = inginious.backend._pool_manager.PoolManager(self._operations_queue, self._done_queue,
                                                               docker_instances, containers_names, tasks_directory, fast_pool_size, slow_pool_size, containers_hard)
        self._pool_manager.start()

        signal.signal(signal.SIGINT, self.cleanup)

        # Start callback managers
        print "Starting callback managers"
        self._callback_manager = []
        for _ in range(callback_manager_count):
            process = CallbackManager(self._done_queue, self._docker_config, self._running_job_data, self._hook_manager)
            self._callback_manager.append(process)
            process.start()

        print "Job Manager initialization done"
        self._hook_manager.call_hook("job_manager_init_done", job_manager=self)

    def cleanup(self, dummy1=None, dummy2=None):
        """ Close the pool manager """
        print "Received exit signal"
        print "Calling job_manager_exit hook"
        self._hook_manager.call_hook("job_manager_exit", job_manager=self)
        print "Tell the pool manager to close itself"
        self._operations_queue.put((CLOSE, []))
        print "Waiting five seconds for the pool manager to close"
        self._pool_manager.join(5)
        if self._pool_manager.is_alive():
            print "Pool manager did not exit. Killing it."
            self._pool_manager.terminate()
            self._pool_manager.join()
        print "Stopping the process sync manager"
        self._memory_manager.shutdown()
        print "Exiting"
        exit(0)

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

        # Check task answer that do not need emulation
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

        if need_emul:
            # Go through the whole process: sent everything to docker
            self._running_job_data[jobid] = (task, callback, basedict, statinfo)
            self._hook_manager.call_hook("new_job", jobid=jobid, task=task, statinfo=statinfo, inputdata=inputdata)
            self._operations_queue.put((RUN_JOB, [jobid, inputdata, os.path.join(self._tasks_directory, task.get_course_id(), task.get_id()), task.get_limits(), task.get_environment(), debug]))
        else:
            # Only send data to a CallbackManager
            basedict["text"] = "\n".join(basedict["text"])
            self._running_job_data[jobid] = (task, callback, basedict, statinfo)
            self._hook_manager.call_hook("new_job", jobid=jobid, task=task, statinfo=statinfo, inputdata=inputdata)
            self._done_queue.put((jobid, None))

        return jobid
