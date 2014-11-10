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
""" Pages that allow editing of tasks """
from collections import OrderedDict
import json
import os.path
import re
from zipfile import ZipFile

import web

from common.base import INGIniousConfiguration, id_checker
from common.task_file_managers.tasks_file_manager import TaskFileManager
from frontend.accessible_time import AccessibleTime
from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
from frontend.custom.tasks import FrontendTask
from frontend.pages.course_admin.utils import get_course_and_check_rights


class CourseEditTask(object):

    """ Edit a task """

    def GET(self, courseid, taskid):
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        course = get_course_and_check_rights(courseid)

        try:
            task_data = TaskFileManager.get_manager(courseid, taskid).read()
        except:
            task_data = None
        if task_data is None:
            task_data = {}
        environments = INGIniousConfiguration["containers"].keys()

        current_filetype = None
        try:
            current_filetype = TaskFileManager.get_manager(courseid, taskid).get_ext()
        except:
            pass
        available_filetypes = TaskFileManager.get_available_file_managers().keys()

        return renderer.admin_course_edit_task(
            course,
            taskid,
            task_data,
            environments,
            json.dumps(
                task_data.get(
                    'problems',
                    {})),
            self.contains_is_html(task_data),
            current_filetype,
            available_filetypes,
            AccessibleTime)

    @classmethod
    def contains_is_html(cls, data):
        """ Detect if the problem has at least one "xyzIsHTML" key """
        for key, val in data.iteritems():
            if key.endswith("IsHTML"):
                return True
            if isinstance(val, (OrderedDict, dict)) and cls.contains_is_html(val):
                return True
        return False

    @classmethod
    def dict_from_prefix(cls, prefix, dictionary):
        """
            >>> from collections import OrderedDict
            >>> od = OrderedDict()
            >>> od["problem[q0][a]"]=1
            >>> od["problem[q0][b][c]"]=2
            >>> od["problem[q1][first]"]=1
            >>> od["problem[q1][second]"]=2
            >>> AdminCourseEditTask.dict_from_prefix("problem",od)
            OrderedDict([('q0', OrderedDict([('a', 1), ('b', OrderedDict([('c', 2)]))])), ('q1', OrderedDict([('first', 1), ('second', 2)]))])
        """
        o_dictionary = OrderedDict()
        for key, val in dictionary.iteritems():
            if key.startswith(prefix):
                o_dictionary[key[len(prefix):].strip()] = val
        dictionary = o_dictionary

        if len(dictionary) == 0:
            return None
        elif len(dictionary) == 1 and "" in dictionary:
            return dictionary[""]
        else:
            return_dict = OrderedDict()
            for key, val in dictionary.iteritems():
                ret = re.search(r"^\[([^\]]+)\](.*)$", key)
                if ret is None:
                    continue
                return_dict[ret.group(1)] = cls.dict_from_prefix("[{}]".format(ret.group(1)), dictionary)
            return return_dict

    def parse_problem(self, problem_content):
        """ Parses a problem, modifying some data """
        del problem_content["@order"]

        if "headerIsHTML" in problem_content:
            problem_content["headerIsHTML"] = True

        if "multiple" in problem_content:
            problem_content["multiple"] = True

        if "centralize" in problem_content:
            problem_content["centralize"] = True

        if "choices" in problem_content:
            problem_content["choices"] = [val for _, val in sorted(problem_content["choices"].iteritems(), key=lambda x: int(x[0]))]
            for choice in problem_content["choices"]:
                if "valid" in choice:
                    choice["valid"] = True
                if "textIsHTML" in choice:
                    choice["textIsHTML"] = True

        if "limit" in problem_content:
            try:
                problem_content["limit"] = int(problem_content["limit"])
            except:
                del problem_content["limit"]

        if "allowed_exts" in problem_content:
            if problem_content["allowed_exts"] == "":
                del problem_content["allowed_exts"]
            else:
                problem_content["allowed_exts"] = problem_content["allowed_exts"].split(',')

        if "max_size" in problem_content:
            try:
                problem_content["max_size"] = int(problem_content["max_size"])
            except:
                del problem_content["max_size"]

        if problem_content["type"] == "custom":
            try:
                custom_content = json.loads(problem_content["custom"])
            except:
                raise Exception("Invalid JSON in custom content")
            problem_content.update(custom_content)
            del problem_content["custom"]

        return problem_content

    def POST(self, courseid, taskid):
        """ Edit a task """
        if not id_checker(taskid) or not id_checker(courseid):
            raise Exception("Invalid course/task id")

        course = get_course_and_check_rights(courseid)

        # Parse content
        try:
            data = web.input(task_file={})

            try:
                task_zip = data.get("task_file").file
            except:
                task_zip = None
            del data["task_file"]

            problems = self.dict_from_prefix("problem", data)
            limits = self.dict_from_prefix("limits", data)

            data = {key: val for key, val in data.iteritems() if not key.startswith("problem") and not key.startswith("limits")}
            del data["@action"]

            try:
                file_manager = TaskFileManager.get_available_file_managers()[data["@filetype"]](courseid, taskid)
            except Exception as inst:
                return json.dumps({"status": "error", "message": "Invalid file type: {}".format(str(inst))})
            del data["@filetype"]

            if problems is None:
                return json.dumps({"status": "error", "message": "You cannot create a task without subproblems"})

            # Order the problems (this line also deletes @order from the result)
            data["problems"] = OrderedDict([(key, self.parse_problem(val))
                                            for key, val in sorted(problems.iteritems(), key=lambda x: int(x[1]['@order']))])
            data["limits"] = limits

            # Accessible
            if data["accessible"] == "custom":
                data["accessible"] = "{}/{}".format(data["accessible_start"], data["accessible_end"])
            elif data["accessible"] == "true":
                data["accessible"] = True
            else:
                data["accessible"] = False
            del data["accessible_start"]
            del data["accessible_end"]

            # Checkboxes
            if data.get("responseIsHTML"):
                data["responseIsHTML"] = True
            if data.get("contextIsHTML"):
                data["contextIsHTML"] = True
        except Exception as message:
            return json.dumps({"status": "error", "message": "Your browser returned an invalid form ({})".format(str(message))})

        # Get the course
        try:
            course = FrontendCourse(courseid)
        except:
            return json.dumps({"status": "error", "message": "Error while reading course's informations"})

        # Get original data
        try:
            orig_data = TaskFileManager.get_manager(courseid, taskid).read()
            data["order"] = orig_data["order"]
        except:
            pass

        try:
            FrontendTask(course, taskid, data)
        except Exception as message:
            return json.dumps({"status": "error", "message": "Invalid data: {}".format(str(message))})

        if not os.path.exists(os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid)):
            os.mkdir(os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid))

        if task_zip:
            try:
                zipfile = ZipFile(task_zip)
            except Exception as message:
                return json.dumps({"status": "error", "message": "Cannot read zip file. Files were not modified"})

            try:
                zipfile.extractall(os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid))
            except Exception as message:
                return json.dumps({"status": "error", "message": "There was a problem while extracting the zip archive. Some files may have been modified"})

        TaskFileManager.delete_all_possible_task_files(courseid, taskid)
        file_manager.write(data)

        return json.dumps({"status": "ok"})
