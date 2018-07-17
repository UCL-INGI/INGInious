# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """
import copy
import json
import logging
import re
import tempfile
from collections import OrderedDict
from zipfile import ZipFile
from natsort import natsorted

import bson
import web
from inginious.frontend.accessible_time import AccessibleTime
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

import inginious.common.custom_yaml
from inginious.common.base import id_checker
from inginious.frontend.pages.course_admin.task_edit_file import CourseTaskFiles
from inginious.frontend.tasks import WebAppTask


class CourseEditTask(INGIniousAdminPage):
    """ Edit a task """
    _logger = logging.getLogger("inginious.webapp.task_edit")

    def GET_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        try:
            task_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
        except:
            task_data = None
        if task_data is None:
            task_data = {}

        environments = self.containers

        current_filetype = None
        try:
            current_filetype = self.task_factory.get_task_descriptor_extension(courseid, taskid)
        except:
            pass
        available_filetypes = self.task_factory.get_available_task_file_extensions()

        additional_tabs = self.plugin_manager.call_hook('task_editor_tab', course=course, taskid=taskid,
                                                        task_data=task_data, template_helper=self.template_helper)

        return self.template_helper.get_renderer().course_admin.task_edit(
            course,
            taskid,
            self.task_factory.get_problem_types(),
            task_data,
            environments,
            task_data.get('problems',{}),
            self.contains_is_html(task_data),
            current_filetype,
            available_filetypes,
            AccessibleTime,
            CourseTaskFiles.get_task_filelist(self.task_factory, courseid, taskid),
            additional_tabs
        )

    @classmethod
    def contains_is_html(cls, data):
        """ Detect if the problem has at least one "xyzIsHTML" key """
        for key, val in data.items():
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
        for key, val in dictionary.items():
            if key.startswith(prefix):
                o_dictionary[key[len(prefix):].strip()] = val
        dictionary = o_dictionary

        if len(dictionary) == 0:
            return None
        elif len(dictionary) == 1 and "" in dictionary:
            return dictionary[""]
        else:
            return_dict = OrderedDict()
            for key, val in dictionary.items():
                ret = re.search(r"^\[([^\]]+)\](.*)$", key)
                if ret is None:
                    continue
                return_dict[ret.group(1)] = cls.dict_from_prefix("[{}]".format(ret.group(1)), dictionary)
            return return_dict

    def parse_problem(self, problem_content):
        """ Parses a problem, modifying some data """
        del problem_content["@order"]
        return self.task_factory.get_problem_types().get(problem_content["type"]).parse_problem(problem_content)

    def wipe_task(self, courseid, taskid):
        """ Wipe the data associated to the taskid from DB"""
        submissions = self.database.submissions.find({"courseid": courseid, "taskid": taskid})
        for submission in submissions:
            for key in ["input", "archive"]:
                if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                    self.submission_manager.get_gridfs().delete(submission[key])

        self.database.aggregations.remove({"courseid": courseid, "taskid": taskid})
        self.database.user_tasks.remove({"courseid": courseid, "taskid": taskid})
        self.database.submissions.remove({"courseid": courseid, "taskid": taskid})

        self._logger.info("Task %s/%s wiped.", courseid, taskid)

    def POST_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid) or not id_checker(courseid):
            raise Exception("Invalid course/task id")

        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        data = web.input(task_file={})

        # Delete task ?
        if "delete" in data:
            self.task_factory.delete_task(courseid, taskid)
            if data.get("wipe", False):
                self.wipe_task(courseid, taskid)
            raise web.seeother(self.app.get_homepath() + "/admin/"+courseid+"/tasks")

        # Else, parse content
        try:
            try:
                task_zip = data.get("task_file").file
            except:
                task_zip = None
            del data["task_file"]

            problems = self.dict_from_prefix("problem", data)
            limits = self.dict_from_prefix("limits", data)
            
            #Tags
            tags = self.dict_from_prefix("tags", data)
            if tags is None:
                tags = {}
            tags = OrderedDict(sorted(tags.items(), key=lambda item: item[0])) # Sort by key
            
            # Repair tags
            for k in tags:
                tags[k]["visible"] = ("visible" in tags[k])  # Since unckecked checkboxes are not present here, we manually add them to avoid later errors
                tags[k]["type"] = int(tags[k]["type"])
                if not "id" in tags[k]:
                    tags[k]["id"] = "" # Since textinput is disabled when the tag is organisational, the id field is missing. We add it to avoid Keys Errors
                if tags[k]["type"] == 2:
                    tags[k]["id"] = "" # Force no id if organisational tag

            # Remove uncompleted tags (tags with no name or no id)
            for k in list(tags.keys()): 
                if (tags[k]["id"] == "" and tags[k]["type"] != 2) or tags[k]["name"] == "":
                    del tags[k]
            
            # Find duplicate ids. Return an error if some tags use the same id.
            for k in tags: 
                if tags[k]["type"] != 2: # Ignore organisational tags since they have no id.
                    count = 0
                    id = str(tags[k]["id"])
                    if (" " in id):
                        return json.dumps({"status": "error", "message": _("You can not use spaces in the tag id field.")})
                    if not id_checker(id):
                        return json.dumps({"status": "error", "message": _("Invalid tag id: {}").format(id)})
                    for k2 in tags:
                        if tags[k2]["type"] != 2 and tags[k2]["id"] == id:
                            count = count+1
                    if count > 1:
                        return json.dumps({"status": "error", "message": _("Some tags have the same id! The id of a tag must be unique.")})                

            data = {key: val for key, val in data.items() if
                    not key.startswith("problem")
                    and not key.startswith("limits")
                    and not key.startswith("tags")
                    and not key.startswith("/")}
            del data["@action"]

            # Determines the task filetype
            if data["@filetype"] not in self.task_factory.get_available_task_file_extensions():
                return json.dumps({"status": "error", "message": _("Invalid file type: {}").format(str(data["@filetype"]))})
            file_ext = data["@filetype"]
            del data["@filetype"]

            # Parse and order the problems (also deletes @order from the result)
            if problems is None:
                return json.dumps({"status": "error", "message": _("You cannot create a task without subproblems")})

            data["problems"] = OrderedDict([(key, self.parse_problem(val))
                                            for key, val in sorted(iter(problems.items()), key=lambda x: int(x[1]['@order']))])

            # Task limits
            data["limits"] = limits
            data["tags"] = OrderedDict(sorted(tags.items(), key=lambda x: x[1]['type']))
            if "hard_time" in data["limits"] and data["limits"]["hard_time"] == "":
                del data["limits"]["hard_time"]

            # Weight
            try:
                data["weight"] = float(data["weight"])
            except:
                return json.dumps({"status": "error", "message": _("Grade weight must be a floating-point number")})

            # Groups
            if "groups" in data:
                data["groups"] = True if data["groups"] == "true" else False

            # Submision storage
            if "store_all" in data:
                try:
                    stored_submissions = data["stored_submissions"]
                    data["stored_submissions"] = 0 if data["store_all"] == "true" else int(stored_submissions)
                except:
                    return json.dumps(
                        {"status": "error", "message": _("The number of stored submission must be positive!")})

                if data["store_all"] == "false" and data["stored_submissions"] <= 0:
                    return json.dumps({"status": "error", "message": _("The number of stored submission must be positive!")})
                del data['store_all']

            # Submission limits
            if "submission_limit" in data:
                if data["submission_limit"] == "none":
                    result = {"amount": -1, "period": -1}
                elif data["submission_limit"] == "hard":
                    try:
                        result = {"amount": int(data["submission_limit_hard"]), "period": -1}
                    except:
                        return json.dumps({"status": "error", "message": _("Invalid submission limit!")})

                else:
                    try:
                        result = {"amount": int(data["submission_limit_soft_0"]), "period": int(data["submission_limit_soft_1"])}
                    except:
                        return json.dumps({"status": "error", "message": _("Invalid submission limit!")})

                del data["submission_limit_hard"]
                del data["submission_limit_soft_0"]
                del data["submission_limit_soft_1"]
                data["submission_limit"] = result
                                
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

            # Network grading
            data["network_grading"] = "network_grading" in data
        except Exception as message:
            return json.dumps({"status": "error", "message": _("Your browser returned an invalid form ({})").format(message)})

        # Get the course
        try:
            course = self.course_factory.get_course(courseid)
        except:
            return json.dumps({"status": "error", "message": _("Error while reading course's informations")})

        # Get original data
        try:
            orig_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
            data["order"] = orig_data["order"]
        except:
            pass

        task_fs = self.task_factory.get_task_fs(courseid, taskid)
        task_fs.ensure_exists()

        # Call plugins and return the first error
        plugin_results = self.plugin_manager.call_hook('task_editor_submit', course=course, taskid=taskid,
                                                       task_data=data, task_fs=task_fs)

        # Retrieve the first non-null element
        error = next(filter(None, plugin_results), None)
        if error is not None:
            return error

        try:
            WebAppTask(course, taskid, data, task_fs, self.plugin_manager, self.task_factory.get_problem_types())
        except Exception as message:
            return json.dumps({"status": "error", "message": _("Invalid data: {}").format(str(message))})

        if task_zip:
            try:
                zipfile = ZipFile(task_zip)
            except Exception:
                return json.dumps({"status": "error", "message": _("Cannot read zip file. Files were not modified")})

            with tempfile.TemporaryDirectory() as tmpdirname:
                try:
                    zipfile.extractall(tmpdirname)
                except Exception:
                    return json.dumps(
                        {"status": "error", "message": _("There was a problem while extracting the zip archive. Some files may have been modified")})
                task_fs.copy_to(tmpdirname)

        self.task_factory.delete_all_possible_task_files(courseid, taskid)
        self.task_factory.update_task_descriptor_content(courseid, taskid, data, force_extension=file_ext)
        course.update_all_tags_cache()
        
        return json.dumps({"status": "ok"})
