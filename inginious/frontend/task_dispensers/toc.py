# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import json
from collections import OrderedDict

from inginious.frontend.task_dispensers.util import check_toc, SectionsList, SectionConfigItem
from inginious.frontend.task_dispensers import TaskDispenser


class TableOfContents(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data, database, course_id):
        self._task_list_func = task_list_func
        self._toc = SectionsList(dispenser_data)
        self._database = database
        self._course_id = course_id

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
        try:
            struct = self._toc.to_structure()
            for elem in struct:
                weight = self._toc.get_value_rec(taskid,elem,"weights")
                if weight is not None:
                    return weight
            return 1
        except:
            return 1

    def get_no_stored_submissions(self,taskid):
        """Returns the maximum stored submission specified by the administrator"""
        try:
            struct = self._toc.to_structure()
            for elem in struct:
                no_stored_submissions = self._toc.get_value_rec(taskid,elem,"no_stored_submissions")
                if no_stored_submissions is not None:
                    return no_stored_submissions
            return 0
        except:
            return 0

    def get_evaluation_mode(self,taskid):
        """Returns the evaluation mode specified by the administrator"""
        try:
            struct = self._toc.to_structure()
            for elem in struct:
                evaluation_mode = self._toc.get_value_rec(taskid,elem,"evaluation_mode")
                if evaluation_mode is not None:
                    return evaluation_mode
            return "best"
        except:
            return "best"

    def get_submission_limit(self, taskid):
        """ Returns the submission limits et for the task"""
        try:
            struct = self._toc.to_structure()
            for elem in struct:
                submission_limit = self._toc.get_value_rec(taskid, elem, "submission_limit")
                if submission_limit is not None:
                    return submission_limit
            return {"amount": -1, "period": -1}
        except:
            return {"amount": -1, "period": -1}

    def get_group_submission(self, taskid):
        """ Indicates if the task submission mode is per groups """
        try:
            struct = self._toc.to_structure()
            for elem in struct:
                group_submission = self._toc.get_value_rec(taskid, elem, "group_submission")
                if group_submission is not None:
                    return group_submission
            return False
        except:
            return False

    def get_categories(self,taskid):
        """Returns the categories specified for the taskid by the administrator"""
        try:
            struct = self._toc.to_structure()
            for elem in struct:
                categories = self._toc.get_value_rec(taskid,elem,"categories")
                if categories is not None:
                    return categories
            return []
        except:
            return []

    def get_all_categories(self):
        """Returns the categories specified by the administrator"""
        tasks = self._toc.get_tasks()
        all_categories = []
        for task in tasks:
            try:
                struct = self._toc.to_structure()
                for elem in struct:
                    categories = self._toc.get_value_rec(task,elem,"categories")
                    if categories is not None:
                        all_categories += categories
            except:
                return all_categories
        return all_categories

    def get_course_grade(self, username):
        """ Returns the grade of a user for the current course"""
        task_list = self.get_user_task_list([username])[username]
        user_tasks = self._database.user_tasks.find({"username": username, "courseid": self._course_id, "taskid": {"$in": task_list}})
        return self._toc.get_course_grade_weighted_sum(user_tasks, task_list, self.get_weight)

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

    @classmethod
    def check_dispenser_data(cls, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        new_toc = json.loads(dispenser_data)
        valid, errors = check_toc(new_toc)
        return new_toc if valid else None, errors


    def get_user_task_list(self, usernames):
        """ Returns a dictionary with username as key and the user task list as value """
        tasks = self._task_list_func()
        task_list = [taskid for taskid in self._toc.get_tasks() if
                     taskid in tasks and tasks[taskid].get_accessible_time().after_start()]
        return {username: task_list for username in usernames}

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        tasks = self._task_list_func()
        return OrderedDict([(taskid, tasks[taskid]) for taskid in self._toc.get_tasks() if taskid in tasks])

    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        tasks_id = self._toc.get_tasks()
        if taskid in tasks_id:
            return tasks_id.index(taskid)
        else:
            return len(tasks_id)