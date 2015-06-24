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
""" Starts an agent """

import logging
import os
from backend_agent.agent import RemoteAgent
import common.base
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="Port to listen to", type=int)
    parser.add_argument("--dir", help="Path to a directory where the agent can store information, such as caches. Defaults to ./agent_data",
                        default="./agent_data")
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    if not os.path.exists(os.path.join(args.dir, 'tasks')):
        os.makedirs(os.path.join(args.dir, 'tasks'))
    if not os.path.exists(os.path.join(args.dir, 'tmp')):
        os.makedirs(os.path.join(args.dir, 'tmp'))

    common.base.init_common_lib(os.path.join(args.dir, 'tasks'), [], 1) # we do not need to upload file, so not needed here

    # create logger
    logger = logging.getLogger("agent")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    RemoteAgent(args.port, os.path.join(args.dir, 'tmp'))