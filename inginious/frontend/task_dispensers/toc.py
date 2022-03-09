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

    @classmethod
    def get_id(cls):
        """ Returns the task dispenser id """
        return "toc"

    @classmethod
    def get_name(cls, language):
        """ Returns the localized task dispenser name """
        return _("Table of contents")

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