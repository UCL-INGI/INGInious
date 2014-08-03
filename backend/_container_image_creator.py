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
""" Contains the function container_image_creator, which is used by JobManager to build new container image on a docker instance """

import json
import os
import docker
from backend._message_types import CONTAINER_IMAGE_BUILT


def container_image_creator(docker_instance_id, docker_configuration, containers_directory, container_names, operations_queue):
    """ Build containers on a remote docker instance.
        Containers must be the keys of the dictionary containers_available, and values must be Event objects.
        Events are set when a container has been built.
    """
    for container in container_names:
        print "building container {} for docker instance {}".format(container, docker_instance_id)
        try:
            build_docker_container(docker_instance_id, docker_configuration, containers_directory, container)
        except Exception as inst:
            print "there was an error while building the container {} for docker instance {}:\n\t\t{}".format(container, docker_instance_id, str(inst))
        finally:
            # Always set the event, even if the build fails.
            operations_queue.put((CONTAINER_IMAGE_BUILT, [docker_instance_id, container]))


def build_docker_container(docker_instance_id, docker_configuration, containers_directory, container):
    """ Ensures a container is up to date """
    docker_connection = docker.Client(base_url=docker_configuration.get('server_url'))
    response = docker_connection.build(path=os.path.join(containers_directory, container), tag=docker_configuration.get("container_prefix", "inginious/") + container, rm=True)
    for i in response:
        if i == "\n" or i == "\r\n":
            continue
        try:
            j = json.loads(i)
        except:
            raise Exception("Error while building {} for docker instance {}: can't read Docker output".format(container, docker_instance_id))
        if 'error' in j:
            raise Exception("Error while building {} for docker instance {}: Docker returned error {}".format(container, docker_instance_id, j["error"]))
