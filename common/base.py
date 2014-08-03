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
""" Basic dependencies for every modules that uses INGInious """
import json
import re


class Configuration(dict):

    """ Config class """

    def load(self, path):
        """ Load the config from a json file """
        self.update(json.load(open(path, "r")))

INGIniousConfiguration = Configuration()


def id_checker(id_to_test):
    """Checks if a id is correct"""
    return bool(re.match(r'[a-z0-9\-_]+$', id_to_test, re.IGNORECASE))
