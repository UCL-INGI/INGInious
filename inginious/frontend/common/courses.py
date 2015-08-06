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
""" Classes modifying basic tasks, problems and boxes classes """
from inginious.common.courses import Course


class FrontendCourse(Course):
    """ A basic course extension that stores the name of the course """
    def __init__(self, courseid, content, task_factory):
        super(FrontendCourse, self).__init__(courseid, content, task_factory)

        try:
            self._name = self._content['name']
        except:
            raise Exception("Course has an invalid description: " + self.get_id())

    def get_name(self):
        """ Return the name of this course """
        return self._name
