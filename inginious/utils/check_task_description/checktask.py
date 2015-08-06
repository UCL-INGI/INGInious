#! /usr/bin/python
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
"""
    Small tool to allow verification of .task and .course files.
"""
import sys
import os

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), '..', '..'))

from inginious.common.course_factory import create_factories
import inginious.frontend.webapp.plugins.task_file_readers.json_reader
import inginious.frontend.webapp.plugins.task_file_readers.rst_reader

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskdir", help="Path to the directory where the courses are stored. Default to ./tasks")
    parser.add_argument("course", help="Course id")
    parser.add_argument("task", help="Task id")
    args = parser.parse_args()

    course_factory, task_factory = create_factories(args.taskdir)

    task_factory.add_custom_task_file_manager(inginious.frontend.webapp.plugins.task_file_readers.json_reader.TaskJSONFileReader())
    task_factory.add_custom_task_file_manager(inginious.frontend.webapp.plugins.task_file_readers.rst_reader.TaskRSTFileReader())

    try:
        course_factory.get_task(args.course, args.task)
    except Exception as inst:
        print "There was an error while validating the file:"
        print type(inst)
        print inst
        exit(1)
    else:
        print "File verification succeeded"
        exit(0)
