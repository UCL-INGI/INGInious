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
""" Contains the submitter function, which is used by PoolManager to run new containers """

import json
import os.path

import docker

from backend._message_types import JOB_LAUNCHED


def submitter(jobid, inputdata, task_directory, limits, environment, debug, docker_config, output_queue):
    """
        Runs a new job.

        Arguments:

        *jobid*
            the jobid.
        *inputdata*
            the input data, as a dictionnary of problemid:problem_answer pairs.
        *task_directory*
            the directory containing the data of the task to run
        *limits*
            the dictionary containing the task's limit
        *environment*
            the image to run the task in
        *debug*
            boolean indicating if the container should return additionnal debug information
        *docker_config*
            docker configuration, as a dict. See the JobManager class.
        *output_queue*
            queue of a Waiter. Will send a tuple (jobid, containerid).
            If an error happens, containerid will be None.

    """
    try:
        docker_connection = docker.Client(base_url=docker_config.get('server_url'))
        mem_limit = limits.get("memory", 100)
        if mem_limit < 20:
            mem_limit = 20

        response = docker_connection.create_container(
            environment,
            stdin_open=True,
            network_disabled=True,
            volumes={'/ro/task': {}},
            mem_limit=mem_limit * 1024 * 1024
        )
        container_id = response["Id"]

        # Start the container
        docker_connection.start(container_id, binds={os.path.abspath(task_directory): {'ro': True, 'bind': '/ro/task'}})

        # Send the input data
        container_input = {"input": inputdata, "limits": limits}
        if debug:
            container_input["debug"] = True
        docker_connection.attach_socket(container_id, {'stdin': 1, 'stream': 1}).send(json.dumps(container_input) + "\n")

        output_queue.put((JOB_LAUNCHED, [jobid, container_id]))
    except:
        print "Container for jobid {} failed to start".format(jobid)
        output_queue.put((JOB_LAUNCHED, [jobid, None]))
