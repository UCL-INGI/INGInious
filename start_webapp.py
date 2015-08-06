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
""" Starts the webapp """

import os
import argparse
from inginious.common.base import load_json_or_yaml

import inginious.frontend.webapp.app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to configuration file. By default: configuration.yaml or configuration.json")
    parser.add_argument("--host", help="Host to bind to", default="localhost")
    parser.add_argument("--port", help="Port to listen to", type=int, default=8080)
    args = parser.parse_args()

    config = None
    if args.config is None:
        if os.path.isfile("./configuration.yaml"):
            config = "./configuration.yaml"
        elif os.path.isfile("./configuration.json"):
            config = "./configuration.json"
        else:
            raise Exception("No configuration file found")

    inginious.frontend.webapp.app.start_app(load_json_or_yaml(config), hostname=args.host, port=args.port)
