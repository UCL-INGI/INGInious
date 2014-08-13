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
"""
    Contains the message types that can be sent to the pool manager's queue.

    RUN_JOB
        Runs a new job
        (RUN_JOB, [jobid, input_data, task_directory, limits, environment, debug])
    JOB_LAUNCHED
        Indicates that a job is now running on a remote docker instance.
        (JOB_LAUNCHED, [jobid, containerid])
    CONTAINER_DONE
        Indicates that a container has finished in the remote docker instance.
        (CONTAINER_DONE, [docker_instance_id, containerid])
    JOB_RESULT
        Returns the job results
        (JOB_RESULT, [jobid, results])
    CLOSE
        Closes the pool manager
        (CLOSE, [])
"""
# Message types
RUN_JOB = 1
JOB_LAUNCHED = 2
CONTAINER_DONE = 3
JOB_RESULT = 4
CLOSE = 5