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
""" Configuration for the frontend. Initialize the common libraries. """
import json
import common.base


class Configuration(dict):

    """ Config class """

    def load(self, path):
        """ Load the config from a json file """
        self.update(json.load(open(path, "r")))
        common.base.init_common_lib(self["tasks_directory"],
                                    self.get('allowed_file_extensions', [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"]),
                                    self.get('max_file_size', 1024 * 1024))

INGIniousConfiguration = Configuration()
