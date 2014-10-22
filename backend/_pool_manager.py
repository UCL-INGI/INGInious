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
""" A manager for process pools """
from collections import deque
import multiprocessing
import signal

from backend._deleter import deleter
from backend._event_reader import event_reader
from backend._message_types import CONTAINER_DONE, JOB_LAUNCHED, JOB_RESULT, RUN_JOB, CLOSE
from backend._result_getter import result_getter
from backend._submitter import submitter


def _init_worker():
    """ Allow processes in pools to ignore SIGINT """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


class PoolManager(multiprocessing.Process):

    """
        Manages two process pools, one for fast operations, the other for operations that takes a longer time.

        Operations to send to the pools are received in a queue. Operations are tuples, which contents are defined in the module _message_type
    """

    def __init__(self, operations_queue, done_queue, docker_instances, container_names, tasks_directory, fast_pool_size=None, slow_pool_size=None, containers_hard=[]):
        multiprocessing.Process.__init__(self)

        self._queue = operations_queue
        self._done_queue = done_queue

        self._fast_pool_size = fast_pool_size
        self._slow_pool_size = slow_pool_size

        self._container_names = container_names
        self._tasks_directory = tasks_directory
        self._docker_config = docker_instances

        self.message_managers = {
            RUN_JOB: PoolManager._run_job,
            JOB_LAUNCHED: PoolManager._job_launched,
            CONTAINER_DONE: PoolManager._container_done,
            JOB_RESULT: PoolManager._job_result,
            CLOSE: PoolManager.close}

        # Jobs waiting for a docker instance
        self._jobs_waiting_for_docker_instance = deque()
        self._jobs_waiting_for_docker_instance_hard = deque()

        self._running_job_count = []
        self._running_job_count_hard = []  # self._running_job_count = self._running_job_count_hard + fast

        self._job_running_on = {}  # jobid:docker_instance_id
        self._job_running_on_container = {}  # jobid:containerid

        self._containers_done = []
        self._containers_launched = []

        self._hard_jobs_id = set()

        self._containers_hard = containers_hard

        # Pools will be started inside the start() method
        self._fast_pool = None
        self._slow_pool = None

    def get_waiting_jobs_count(self):
        """Returns the total number of waiting jobs in the Pool Manager"""
        result = 0
        for item in self._running_job_count:
            result += item
        return result

    def _get_docker_instance_and_inc(self, hard):
        """ Return the id of a docker instance and increment the job count associated """
        available_instances = [
            (entry, count) for entry, count in enumerate(self._running_job_count)
            if (self._docker_config[entry].get("max_concurrent_jobs", 100) == 0 or self._docker_config[entry].get("max_concurrent_jobs", 100) > count) and
            (not hard or self._docker_config[entry].get("max_concurrent_hard_jobs", 10) == 0 or
             self._docker_config[entry].get("max_concurrent_hard_jobs", 10) > self._running_job_count_hard[entry])
        ]
        if not len(available_instances):
            return None
        min_index, min_value = min(available_instances, key=lambda p: p[1])
        self._running_job_count[min_index] = min_value + 1
        if hard:
            self._running_job_count_hard[min_index] = min_value + 1
        return min_index

    def close(self, dummy1=None, dummy2=None):
        """ Closes the pool manager"""
        print "Terminating pools"
        self._fast_pool.terminate()
        self._slow_pool.terminate()
        print "Waiting for fast pool"
        self._fast_pool.join()
        print "Waiting for slow pool"
        self._slow_pool.join()
        print "Closing pool manager"
        exit(0)

    def run(self):
        # Pools have to be started inside the run function, as it is the first to be run inside the process
        print "Starting pools"
        self._fast_pool = multiprocessing.Pool(self._fast_pool_size, _init_worker)
        self._slow_pool = multiprocessing.Pool(self._slow_pool_size, _init_worker)

        signal.signal(signal.SIGINT, signal.SIG_IGN)

        for docker_instance_id, docker_config in enumerate(self._docker_config):
            self._containers_done.append([])
            self._containers_launched.append({})
            self._running_job_count.append(0)
            self._running_job_count_hard.append(0)

        print "Starting event readers"
        for docker_instance_id, docker_config in enumerate(self._docker_config):
            self._slow_pool.apply_async(event_reader, [docker_instance_id, docker_config, self._queue])

        while True:
            try:
                message_type, message = self._queue.get()
                message_manager = self.message_managers[message_type]
                message_manager(self, message)
            except (IOError, EOFError):
                self.close()
                return

    def _run_job(self, job):
        """ Manages RUN_JOB. Runs a new job"""
        jobid, input_data, task_directory, limits, environment, debug = job

        is_hard = environment in self._containers_hard or limits.get("hard", False)
        docker_instance = self._get_docker_instance_and_inc(is_hard)
        if docker_instance is None:
            if is_hard:
                self._jobs_waiting_for_docker_instance_hard.append(job)
            else:
                self._jobs_waiting_for_docker_instance.append(job)
        else:
            self._job_running_on[jobid] = docker_instance
            self._run_job_real(job, docker_instance)

    def _job_launched(self, message):
        """ Manages JOB_LAUNCHED. Get the result of the job if the container has already finished, or put it in a wait state """
        jobid, containerid = message
        if containerid is None:
            self._done_queue.put((jobid, {"result": "crash", "text": "Cannot start the container"}))
            del self._job_running_on[jobid]
        else:
            self._job_running_on_container[jobid] = containerid

            if containerid in self._containers_done[self._job_running_on[jobid]]:
                self._start_get_result(jobid, containerid)
                self._containers_done[self._job_running_on[jobid]].remove(containerid)
            else:
                self._containers_launched[self._job_running_on[jobid]][containerid] = jobid

    def _container_done(self, message):
        """ Manages CONTAINER_DONE. Get the result if the job was waiting for completion,
            or put the container in a list that will be read when
            the JOB_LAUNCHED message will be received. """
        docker_instance_id, containerid = message
        if containerid in self._containers_launched[docker_instance_id]:
            self._start_get_result(self._containers_launched[docker_instance_id][containerid], containerid)
            del self._containers_launched[docker_instance_id][containerid]
        else:
            self._containers_done[docker_instance_id].append(containerid)

    def _job_result(self, message):
        """ Manages JOB_RESULT. Sent the data to the main process and deletes the container """
        jobid, result = message
        self._done_queue.put((jobid, result))
        self._slow_pool.apply_async(deleter, [self._docker_config[self._job_running_on[jobid]], self._job_running_on_container[jobid]])

        was_hard = jobid in self._hard_jobs_id
        self._running_job_count[self._job_running_on[jobid]] = self._running_job_count[self._job_running_on[jobid]] - 1
        if was_hard:
            self._running_job_count_hard[self._job_running_on[jobid]] = self._running_job_count_hard[self._job_running_on[jobid]] - 1
            self._hard_jobs_id.discard(jobid)

        del self._job_running_on[jobid]
        del self._job_running_on_container[jobid]

        # If the job was slow, we can run another slow job
        if was_hard:
            if len(self._jobs_waiting_for_docker_instance_hard) != 0:
                self._run_job(self._jobs_waiting_for_docker_instance_hard.popleft())
                return

        # Else, run a fast job
        if len(self._jobs_waiting_for_docker_instance) != 0:
            self._run_job(self._jobs_waiting_for_docker_instance.popleft())

    def _start_get_result(self, jobid, containerid):
        """ Runs a result_getter in the fast_pool """
        self._fast_pool.apply_async(result_getter, [jobid, containerid, self._docker_config[self._job_running_on[jobid]], self._queue])

    def _run_job_real(self, job, docker_instance):
        """ Runs a job """
        jobid, input_data, task_directory, limits, environment, debug = job
        if environment in self._containers_hard or limits.get("hard", False):
            self._hard_jobs_id.add(jobid)
        self._fast_pool.apply_async(submitter, [jobid, input_data, task_directory, limits, self._container_names.get(environment, 'default'), debug, self._docker_config[docker_instance], self._queue])
