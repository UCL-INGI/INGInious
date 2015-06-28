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
""" Starts the frontend """

import frontend.app
import os

if __name__ == "__main__":
    if os.path.isfile("./configuration.yaml"):
        frontend.app.start_app("./configuration.yaml")
    elif os.path.isfile("./configuration.json"):
        frontend.app.start_app("./configuration.json")
    else:
        raise Exception("No configuration file found")