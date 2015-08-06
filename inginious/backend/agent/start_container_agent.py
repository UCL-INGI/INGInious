#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
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
""" Used in containers to start an agent """

import sys
import os

sys.path.append('/agent')

import logging
import docker
from docker.utils import kwargs_from_env
from inginious.common.course_factory import create_factories

from inginious.backend.agent.remote_agent import RemoteAgent

if __name__ == "__main__":
    course_factory, task_factory = create_factories("./tasks")

    # create logger
    logger = logging.getLogger("agent")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # tmp dir should be "bindable" by other containers. As the agent runs in a container, we have to guess in which dir
    # /agent_volume is really mounted on, and emulate its presence in the container with a symlink.
    docker_connection = None
    mounted_dir = None

    try:
        docker_connection = docker.Client(**kwargs_from_env())
    except:
        logger.error("Cannot connect to Docker!")
        exit(1)

    try:
        mounted_dir = docker_connection.inspect_container(os.environ["AGENT_CONTAINER_NAME"])["Volumes"]["/agent_volume"]
    except:
        logger.error("Cannot find this container or /agent_volume not mounted")
        exit(1)

    base = os.path.abspath(os.path.join(mounted_dir, "../"))
    if not os.path.exists(base):
        os.makedirs(base)
    if not os.path.exists(mounted_dir):
        os.symlink("/agent_volume", mounted_dir)

    RemoteAgent(int(os.environ["AGENT_PORT"]), "./tasks", course_factory, task_factory, mounted_dir, True)
