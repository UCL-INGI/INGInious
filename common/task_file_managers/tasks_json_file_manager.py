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
""" JSON task file manager """
import collections
import json

from common.task_file_managers.tasks_file_manager import TaskFileManager


class TaskJSONFileManager(TaskFileManager):

    """ Read and write task descriptions in JSON """

    def _get_content(self, content):
        return json.loads(content, object_pairs_hook=collections.OrderedDict)

    @classmethod
    def get_ext(cls):
        return "json"

    def _generate_content(self, data):
        return json.dumps(data, sort_keys=False, indent=4, separators=(',', ': '))
