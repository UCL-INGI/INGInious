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
import math
import os.path
import threading
import time

import docker
from docker.utils import kwargs_from_env
import multiprocessing

from cgutils import cgroup


def _recursive_find_docker_group(cg):
    """ Recursively search for the docker subgroup in the group given """
    if cg.name == "docker":
        return cg
    for child in cg.childs:
        g = _recursive_find_docker_group(child)
        if g is not None:
            return g
    return None


def get_cgroups_docker():
    """ Returns the two groups of docker (with the subsytems cpuacct et memory) """
    cpuacct = cgroup.scan_cgroups('cpuacct')
    memory = cgroup.scan_cgroups('cpuacct')
    d_cpuacct = _recursive_find_docker_group(cpuacct)
    d_memory = _recursive_find_docker_group(memory)

    return d_cpuacct, d_memory


class CGroupTimeoutWatcher(threading.Thread):

    """ Watch the cgroups cpuacct and ask to stop containers when they use too many ressources """

    def __init__(self):
        threading.Thread.__init__(self)

        self._cpu_count = multiprocessing.cpu_count()

        self._docker_cpuacct, _ = get_cgroups_docker()
        if self._docker_cpuacct is None:
            raise Exception("Cannot find the docker cgroups!")
        self._docker_cpuacct = self._docker_cpuacct.fullpath

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
        while(True):
            ltime, container_id, max_time = self._input_queue.get()
            time_diff = ltime - time.time()
            if time_diff > 0:  # we still have to wait
                self._input_queue.put((ltime, container_id, max_time))
                time.sleep(min(time_diff, 5))  # wait maximum for 5 seconds
            else:
                try:
                    usage = float(cgroup.get_cgroup(os.path.join(self._docker_cpuacct, container_id)).get_stats()['usage'])
                except:
                    continue  # container has closed

                print "Current usage: {}. Max: {}".format((usage / (10 ** 9)), max_time)

                if (usage / (10 ** 9)) < max_time:  # retry
                    minimum_remaining_time = math.ceil((max_time - (usage / (10 ** 9))) / self._cpu_count)
                    self._input_queue.put((time.time() + minimum_remaining_time, container_id, max_time))
                else:  # kill it (with fire!)
                    try:
                        docker_connection = docker.Client(**kwargs_from_env())
                        docker_connection.kill(container_id)
                    except:
                        pass
