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
""" Contains result_getter, which retrieves the result of a container """
import json

import docker

from backend._message_types import JOB_RESULT


def result_getter(jobid, containerid, docker_config, output_queue):
    """ Gets the results from a container """
    try:
        docker_connection = docker.Client(base_url=docker_config.get('server_url'))
        stdout = str(docker_connection.logs(containerid, stdout=True, stderr=False))
        stderr = str(docker_connection.logs(containerid, stdout=False, stderr=True))
        if stderr != "":
            print "STDERR: " + stderr

        try:
            result = json.loads(stdout)
            output_queue.put((JOB_RESULT, [jobid, result]))
        except:
            output_queue.put((JOB_RESULT, [jobid, {"result": "crash", "text": "The container returned a badly formatted JSON. Please contact your course administrator."}]))
    except:
        output_queue.put((JOB_RESULT, [jobid, {"result": "crash", "text": "An error occured while contacting Docker. Please retry later."}]))
