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
""" Some helpers to manage cgroups"""

from Queue import PriorityQueue
import logging
import math
import multiprocessing
import os.path
import select
import threading
import time

import docker
from docker.utils import kwargs_from_env

from cgutils import cgroup


def get_container_cgroup(cgroupname, container):
    def recur(cg):
        if cg.name == container or cg.name == "docker-{}.scope".format(container):
            return cg
        else:
            for child in cg.childs:
                g = recur(child)
                if g is not None:
                    return g
        return None

    cgroup_obj = cgroup.scan_cgroups(cgroupname)
    return recur(cgroup_obj)


class CGroupMemoryWatcher(threading.Thread):
    """ Watch for cgroups events on memory """

    logger = logging.getLogger("agent.memory")

    def __init__(self):
        threading.Thread.__init__(self)

        self._update_pipe = os.pipe()
        self._containers_running = {}
        self._containers_running_lock = threading.Lock()

        self.daemon = True

    def add_container_memory_limit(self, container_id, max_memory):
        """ Creates a watcher over the memory used by container_id """

        cg = get_container_cgroup("memory", container_id)
        with self._containers_running_lock:
            self._containers_running[container_id] = {"eventlistener": cgroup.EventListener(cg, 'memory.oom_control'),
                                                      # 'memory.memsw.usage_in_bytes'),
                                                      "killed": False,
                                                      "max_memory": max_memory * 1024 * 1024}
            self._containers_running[container_id]["eventlistener"].register([max_memory * 1024 * 1024])

            # Write a byte to _update_event_descriptor, waking up the select() call
            os.write(self._update_pipe[1], '0')

    def container_had_error(self, container_id):
        """ Returns True if the container was killed due to an OOM. Deletes the watcher on the container memory """
        with self._containers_running_lock:
            if container_id in self._containers_running:
                killed = self._containers_running[container_id]["killed"]
                max_memory = self._containers_running[container_id]["max_memory"]
                del self._containers_running[container_id]

                # Write a byte to _update_event_descriptor, waking up the select() call
                os.write(self._update_pipe[1], '0')

                # Reverify the status of the memory at the end, to be sure about it ;-)
                if not killed:
                    mem_usage = 0
                    try:
                        mem_usage = self._get_max_memory_usage(container_id)
                    except:
                        pass
                    killed = mem_usage > max_memory

                return killed
        return False

    def _get_max_memory_usage(self, container_id):
        """ Return the maximum memory usage of the container, in bytes """
        return int(get_container_cgroup("memory", container_id).get_stats()['memsw.max_usage_in_bytes'])

    def run(self):
        while (True):
            # Get a list with all the eventfd
            with self._containers_running_lock:
                to_select = [self._update_pipe[0]] + [d["eventlistener"].event_fd for d in self._containers_running.values() if
                                                      d["eventlistener"] is not None]

            # Run the select() system call on all the eventfd.
            rlist, _, xlist = select.select(to_select, [], [])

            # First, handle xlist, by deleting the bad eventfds
            if len(xlist) != 0:
                if self._update_pipe[0] in xlist:
                    raise Exception("CGroupMemoryWatcher: critical error, self._update_event_descriptor in xlist")
                with self._containers_running_lock:
                    container_ids = [container_id for container_id, data in self._containers_running
                                     if (data["eventlistener"] is not None and data["eventlistener"].event_fd in rlist)]
                    for container_id in container_ids:
                        self._containers_running[container_id]["eventlistener"] = None

            # If _update_event_descriptor is activated, just read a byte then restart select with a new
            # list of file descriptors
            if self._update_pipe[0] in rlist:
                os.read(self._update_pipe[0], 1)

            # Else, we have to kill some containers...
            elif len(rlist) != 0:
                containers_to_kill = set()
                with self._containers_running_lock:
                    container_ids = [
                        (container_id,
                         d["eventlistener"].event_fd,
                         d["max_memory"]) for container_id,
                                              d in self._containers_running.iteritems() if (
                            d["eventlistener"] is not None and d["eventlistener"].event_fd in rlist)]
                    for container_id, event_fd, max_memory in container_ids:
                        # we have to read everything
                        os.read(event_fd, 64 / 8)

                        mem_usage = -1
                        try:
                            mem_usage = self._get_max_memory_usage(container_id)
                        except:
                            pass

                        if mem_usage != -1:
                            self.logger.info("Deleting container %s as it exhausted its memory limit: %f/%f. Killing it.", container_id, mem_usage,
                                             max_memory)
                            self._containers_running[container_id]["eventlistener"] = None
                            self._containers_running[container_id]["killed"] = True
                            containers_to_kill.add(container_id)

                docker_connection = docker.Client(**kwargs_from_env())
                for container_id in containers_to_kill:
                    try:
                        docker_connection.kill(container_id)
                    except:
                        pass


class CGroupTimeoutWatcher(threading.Thread):
    """ Watch the cgroups cpuacct and ask to stop containers when they use too many ressources """

    logger = logging.getLogger("agent.timeout")

    def __init__(self):
        threading.Thread.__init__(self)

        self._cpu_count = multiprocessing.cpu_count()

        self._input_queue = PriorityQueue()
        self._container_errors = set()

        self.daemon = True

    def container_had_error(self, container_id):
        """ Returns True if the container was killed due to a timeout """
        if container_id in self._container_errors:
            self._container_errors.remove(container_id)
            return True
        return False

    def add_container_timeout(self, container_id, max_time, max_time_hard):
        """ Add a container to watch for, with a timeout of max_time (based on the CPU usage) and a timeout of max_time_hard (in realtime)"""
        self._input_queue.put((time.time(), container_id, max_time))
        self._input_queue.put((time.time() + max_time_hard, container_id, 0))

    def run(self):
        while (True):
            ltime, container_id, max_time = self._input_queue.get()
            time_diff = ltime - time.time()
            if time_diff > 0:  # we still have to wait
                self._input_queue.put((ltime, container_id, max_time))
                time.sleep(min(time_diff, 5))  # wait maximum for 5 seconds
            else:
                try:
                    usage = float(get_container_cgroup("cpuacct", container_id).get_stats()['usage'])
                except:
                    continue  # container has closed

                self.logger.debug("Current time usage: %f. Max: %f.", (usage / (10 ** 9)), max_time)

                if (usage / (10 ** 9)) < max_time:  # retry
                    minimum_remaining_time = math.ceil((max_time - (usage / (10 ** 9))) / self._cpu_count)
                    self.logger.debug("Minimum wait: %f.", minimum_remaining_time)
                    self._input_queue.put((time.time() + minimum_remaining_time, container_id, max_time))
                else:  # kill it (with fire!)
                    self.logger.info("Killing container %s due to timeout", container_id)
                    self._container_errors.add(container_id)
                    try:
                        docker_connection = docker.Client(**kwargs_from_env())
                        docker_connection.kill(container_id)
                    except:
                        pass
