# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """
from inginious.frontend.common.tasks import FrontendTask
from inginious.frontend.webapp.accessible_time import AccessibleTime


class WebAppTask(FrontendTask):
    """ A task that stores additional context information, specific to the web app """

    def __init__(self, course, taskid, content, directory_path, task_problem_types=None):
        super(WebAppTask, self).__init__(course, taskid, content, directory_path, task_problem_types)

        # Grade weight
        self._weight = float(self._data.get("weight", 1.0))

        # _accessible
        self._accessible = AccessibleTime(self._data.get("accessible", None))

        # Order
        self._order = int(self._data.get('order', -1))

        # Group task
        self._groups = bool(self._data.get("groups", False))

        # Default download
        self._evaluate = self._data.get("evaluate", "best")

        # Submission storage
        self._store_only_last = bool(self._data.get("store_only_last", False))

    def get_order(self):
        """ Get the position of this task in the course """
        return self._order

    def get_grading_weight(self):
        """ Get the relative weight of this task in the grading """
        return self._weight

    def get_accessible_time(self):
        """  Get the accessible time of this task """
        return self._accessible

    def is_visible_by_students(self):
        """ Returns true if the task is accessible by all students that are not administrator of the course """
        return self.get_course().is_open_to_non_staff() and self._accessible.after_start()

    def get_deadline(self):
        """ Returns a string containing the deadline for this task """
        if self._accessible.is_always_accessible():
            return "No deadline"
        elif self._accessible.is_never_accessible():
            return "It's too late"
        else:
            return self._accessible.get_end_date().strftime("%d/%m/%Y %H:%M:%S")

    def is_group_task(self):
        """ Indicates if the task submission mode is per groups """
        return self._groups

    def get_evaluate(self):
        """ Indicates the default download for the task """
        return self._evaluate

    def get_store_only_last(self):
        """ Indicates if only the last submission must be stored for the task """
        return self._store_only_last
