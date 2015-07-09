#! /usr/bin/env/python
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
""" Convert all RST/JSON task files to YAML and deletes all *IsHTML fields """

import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), '..', '..'))

from common.task_file_managers.manage import add_custom_task_file_manager, delete_all_possible_task_files, get_task_file_manager
from common.task_file_managers.yaml_manager import TaskYAMLFileManager
import frontend.plugins.task_file_managers.json_manager
import frontend.plugins.task_file_managers.rst_manager
import common.base
from common.courses import Course
import argparse
import tidylib

def add_raw_to_html(field_content):
    """ Convert a HTML field to an RST one, using ".. raw:: html" """
    out, dummy = tidylib.tidy_fragment(field_content)
    rst = ".. raw:: html\n\n"
    for line in out.split('\n'):
        rst += "    "+line+"\n"
    rst += "\n"
    return rst

def convert_field(is_html_field, field, data):
    """ Convert fields """
    if is_html_field in data:
        if data[is_html_field]:
            data[field] = add_raw_to_html(data.get(field, ""))
        del data[is_html_field]

def convert_html(data):
    """ Remove all *IsHTML from a task description """
    convert_field("contextIsHTML", "context", data)
    for p in data.get("problems", {}):
        convert_field("headerIsHTML", "header", data["problems"][p])
        for c in data["problems"][p].get("choices", []):
            convert_field("textIsHTML", "text", c)
        for b in data["problems"][p].get("boxes", {}):
            convert_field("contentIsHTML", "content", data["problems"][p]["boxes"][b])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks", help="Path to the tasks directory to update (the one containing the courses)")
    parser.add_argument("--delete-html", help="Delete *IsHTML fields. Default to false", dest='html', action='store_true', default=False)
    parser.add_argument("--convert-yaml", help="Force conversion to YAML. Default to false", dest='yaml', action='store_true', default=False)
    args = parser.parse_args()

    if args.html is False and args.yaml is False:
        print "Please select at least one of --delete-html and --yaml-convert. See task_converter.py --help"
        exit(1)

    # Init common
    common.base.init_common_lib(args.tasks, [], 1)  # we do not need to upload file, so not needed here
    add_custom_task_file_manager(frontend.plugins.task_file_managers.json_manager.TaskJSONFileManager)
    add_custom_task_file_manager(frontend.plugins.task_file_managers.rst_manager.TaskRSTFileManager)

    courses = Course.get_all_courses()
    for courseid, course in courses.iteritems():
        for taskid, task in course.get_tasks().iteritems():
            data = get_task_file_manager(courseid, taskid).read()

            # Convert *IsHTML if needed
            if args.html:
                convert_html(data)

            # Save
            if not args.yaml: #in original format
                get_task_file_manager(courseid, taskid).write(data)
            else: #force YAML
                delete_all_possible_task_files(courseid, taskid)
                TaskYAMLFileManager(courseid, taskid).write(data)