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
""" Contains the function _event_reader, which returns when containers are done. """
import json

import docker

from inginious.backend._message_types import CONTAINER_DONE


def event_reader(docker_instance_id, docker_config, output_queue):
    """ Read the event stream of docker to detect containers that have done their work """
    print "Event reader for instance {} started".format(docker_instance_id)
    docker_connection = docker.Client(base_url=docker_config.get('server_url'))
    for event in docker_connection.events():
        try:
            event = json.loads(event)
            if event.get("status") == "die":
                output_queue.put((CONTAINER_DONE, [docker_instance_id, event.get("id")]))
        except:
            print "Cannot read docker event {}".format(event)
