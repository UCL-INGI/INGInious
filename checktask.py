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
"""
    Small tool to allow verification of .task and .course files.
    Usage:
        python checktask.py file.task
        python checktask.py file.course
"""
import sys

from frontend.custom.courses import FrontendCourse
from frontend.custom.tasks import FrontendTask
import common.base


def usage():
    """ Usage """
    print "Usage: "
    print "\tpython checktask.py task_directory courseid taskid"
    print "\tpython checktask.py task_directory courseid"
    exit(1)

if len(sys.argv) not in [3, 4]:
    usage()

# Change default path to task Directory
common.base.INGIniousConfiguration["allow_html"] = "tidy"
common.base.INGIniousConfiguration["tasks_directory"] = sys.argv[1]

try:
    if len(sys.argv) == 2:
        FrontendCourse(sys.argv[2])
    else:
        FrontendTask(FrontendCourse(sys.argv[2]), sys.argv[3])
except Exception as inst:
    print "There was an error while validating the file:"
    print inst
    exit(1)
else:
    print "File verification succeeded"
    exit(0)
