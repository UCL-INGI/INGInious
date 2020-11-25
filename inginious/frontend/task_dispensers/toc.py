# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import json
from collections import OrderedDict

from inginious.common.toc import check_toc
from inginious.common.toc import SectionsList
from inginious.frontend.task_dispensers import TaskDispenser


class TableOfContents(TaskDispenser):

    def __init__(self, course_tasks, dispenser_data):
        self._task_list = course_tasks
        self._toc = SectionsList(dispenser_data)

    @classmethod
    def get_id(cls):
        return "toc"

    def get_dispenser_data(self):
        return self._toc

    def render_edit(self, template_helper, course, task_data):
        """ Returns the formatted task list edition form """
        return template_helper.get_renderer(with_layout=False).course_admin.task_dispensers.toc(
            course, self._toc, task_data)

    def render(self, template_helper, course, tasks_data, tag_list):
        """ Returns the formatted task list"""
        return template_helper.get_renderer(with_layout=False).task_dispensers.toc(
            course, self._task_list, tasks_data, tag_list, self._toc)

    @classmethod
    def check_dispenser_data(cls, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        new_toc = json.loads(dispenser_data)
        valid, errors = check_toc(new_toc)
        return new_toc if valid else None, errors

    def filter_accessibility(self, taskid, username):
        """ Returns true if the task is accessible by all students that are not administrator of the course """
        return True

    def get_ordered_tasks(self):
        return OrderedDict(sorted(list(self._task_list.items()), key=lambda t: (self.get_task_order(t[1].get_id()), t[1].get_id())))

    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        tasks_id = self._toc.get_tasks()
        if taskid in tasks_id:
            return tasks_id.index(taskid)
        else:
            return len(tasks_id)