# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import json
from collections import OrderedDict

from inginious.frontend.task_dispensers.util import check_toc, parse_tasks_config, check_task_config,\
    SectionsList, SectionConfigItem, get_course_grade_weighted_sum
from inginious.frontend.task_dispensers import TaskDispenser
from inginious.frontend.accessible_time import AccessibleTime


class TableOfContents(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data, database, course_id):
        # Check dispenser data structure
        dispenser_data = dispenser_data or {"toc": {}, "config": {}}
        if not isinstance(dispenser_data, dict) or "toc" not in dispenser_data or "config" not in dispenser_data:
            raise Exception("Invalid dispenser data structure")

        TaskDispenser.__init__(self, task_list_func, dispenser_data, database, course_id)
        self._toc = SectionsList(dispenser_data.get("toc", {}))
        self._task_config = dispenser_data.get("config", {})
        parse_tasks_config(self._task_config)

    @classmethod
    def get_id(cls):
        """ Returns the task dispenser id """
        return "toc"

    @classmethod
    def get_name(cls, language):
        """ Returns the localized task dispenser name """
        return _("Table of contents")

    def get_weight(self, taskid):
        """ Returns the weight of taskid """
        return self._task_config.get(taskid, {}).get("weight", 1)

    def get_no_stored_submissions(self,taskid):
        """Returns the maximum stored submission specified by the administrator"""
        return self._task_config.get(taskid, {}).get("no_stored_submissions", 0)

    def get_evaluation_mode(self,taskid):
        """Returns the evaluation mode specified by the administrator"""
        return self._task_config.get(taskid, {}).get("evaluation_mode", "best")

    def get_submission_limit(self, taskid):
        """ Returns the submission limits et for the task"""
        return self._task_config.get(taskid, {}).get("submission_limit",  {"amount": -1, "period": -1})

    def get_group_submission(self, taskid):
        """ Indicates if the task submission mode is per groups """
        return self._task_config.get(taskid, {}).get("group_submission", False)

    def get_accessibilities(self, taskids, usernames):
        """  Get the accessible time of this task """
        return {username: {taskid: AccessibleTime(self._task_config.get(taskid, {}).get("accessible", False))
                             for taskid in taskids } for username in usernames}

    def get_deadline(self, taskid, username):
        """ Returns a string containing the deadline for this task """
        accessible_time = self.get_accessibility(taskid, username)
        if accessible_time.is_always_accessible():
            return _("No deadline")
        elif accessible_time.is_never_accessible():
            return _("It's too late")
        else:
            # Prefer to show the soft deadline rather than the hard one
            return accessible_time.get_soft_end_date().strftime("%d/%m/%Y %H:%M:%S")

    def get_categories(self, taskid):
        """Returns the categories specified for the taskid by the administrator"""
        return self._task_config.get(taskid, {}).get("categories", [])

    def get_all_categories(self):
        """Returns the categories specified by the administrator"""
        tasks = self._toc.get_tasks()
        all_categories = []
        for task in tasks:
            try:
                struct = self._toc.to_structure()
                for elem in struct:
                    categories = self._toc.get_value_rec(task, elem, "categories")
                    if categories is not None:
                        all_categories += categories
            except:
                return all_categories
        return all_categories

    def get_course_grade(self, username):
        """ Returns the grade of a user for the current course"""
        task_list = self.get_user_task_list([username])[username]
        user_tasks = self._database.user_tasks.find(
            {"username": username, "courseid": self._course_id, "taskid": {"$in": task_list}})
        return get_course_grade_weighted_sum(user_tasks, task_list, self.get_weight)

    def get_dispenser_data(self):
        """ Returns the task dispenser data structure """
        return self._toc

    def render_edit(self, template_helper, course, task_data):
        """ Returns the formatted task list edition form """
        config_fields = {
            "closed": SectionConfigItem(_("Closed by default"), "checkbox", False)
        }
        return template_helper.render("course_admin/task_dispensers/toc.html", course=course,
                                      course_structure=self._toc, tasks=task_data, config_fields=config_fields)

    def render(self, template_helper, course, tasks_data, tag_list):
        """ Returns the formatted task list"""
        return template_helper.render("task_dispensers/toc.html", course=course, tasks=self._task_list_func(),
                                      tasks_data=tasks_data, tag_filter_list=tag_list, sections=self._toc)

    def check_dispenser_data(self, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        new_toc = json.loads(dispenser_data)
        valid, errors = check_toc(new_toc.get("toc", {}))
        if valid:
            valid, errors = check_task_config(new_toc.get("config", {}))
        return new_toc if valid else None, errors

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        tasks = self._task_list_func()
        return OrderedDict([(taskid, tasks[taskid]) for taskid in self._toc.get_tasks() if taskid in tasks])
