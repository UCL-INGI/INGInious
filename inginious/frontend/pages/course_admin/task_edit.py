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

from inginious.common.base import dict_from_prefix
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
            if isinstance(key, str) and key.endswith("IsHTML"):
                return True
            if isinstance(val, (OrderedDict, dict)) and cls.contains_is_html(val):
                return True
        return False

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

            problems = dict_from_prefix("problem", data)
            limits = dict_from_prefix("limits", data)

            data = {key: val for key, val in data.items() if
                    not key.startswith("problem")
                    and not key.startswith("limits")
                    and not key.startswith("/")}
            del data["@action"]

            # Determines the task filetype
            if data["@filetype"] not in self.task_factory.get_available_task_file_extensions():
                return json.dumps({"status": "error", "message": _("Invalid file type: {}").format(str(data["@filetype"]))})
            file_ext = data["@filetype"]
            del data["@filetype"]

            # Parse and order the problems (also deletes @order from the result)
            if problems is None:
                data["problems"] = OrderedDict([])
            else:
                data["problems"] = OrderedDict([(key, self.parse_problem(val))
                                                for key, val in sorted(iter(problems.items()), key=lambda x: int(x[1]['@order']))])

            # Categories
            course_tags = course.get_tags()
            data['categories'] = [cat for cat in map(str.strip, data['categories'].split(',')) if cat]
            for category in data['categories']:
                if category not in course_tags:
                    return json.dumps({"status": "error", "message": _("Unknown category tag.")})

            # Task limits
            data["limits"] = limits
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

            # Submission storage
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
                data["accessible"] = "{}/{}/{}".format(data["accessible_start"], data["accessible_soft_end"], data["accessible_end"])
            elif data["accessible"] == "true":
                data["accessible"] = True
            else:
                data["accessible"] = False
            del data["accessible_start"]
            del data["accessible_end"]
            del data["accessible_soft_end"]

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
            WebAppTask(course, taskid, data, task_fs, None, self.plugin_manager, self.task_factory.get_problem_types())
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

        return json.dumps({"status": "ok"})
