# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """
from inginious.frontend.common.tasks import FrontendTask
from inginious.frontend.webapp.accessible_time import AccessibleTime


class WebAppTask(FrontendTask):
    """ A task that stores additional context information, specific to the web app """

    def __init__(self, course, taskid, content, directory_path, hook_manager, task_problem_types=None):
        super(WebAppTask, self).__init__(course, taskid, content, directory_path, hook_manager, task_problem_types)

        # Grade weight
        self._weight = float(self._data.get("weight", 1.0))

        # _accessible
        self._accessible = AccessibleTime(self._data.get("accessible", None))

        # Group task
        self._groups = bool(self._data.get("groups", False))

        # Submission limits
        self._submission_limit = self._data.get("submission_limit", {"amount": -1, "period": -1})

    def get_grading_weight(self):
        """ Get the relative weight of this task in the grading """
        return self._weight

    def get_accessible_time(self, plugin_override=True):
        """  Get the accessible time of this task """
        vals = self._hook_manager.call_hook('task_accessibility', course=self.get_course(), task=self, default=self._accessible)
        return vals[0] if len(vals) and plugin_override else self._accessible

    def is_visible_by_students(self):
        """ Returns true if the task is accessible by all students that are not administrator of the course """
        return self.get_course().is_open_to_non_staff() and self.get_accessible_time().after_start()

    def get_deadline(self):
        """ Returns a string containing the deadline for this task """
        if self.get_accessible_time().is_always_accessible():
            return "No deadline"
        elif self.get_accessible_time().is_never_accessible():
            return "It's too late"
        else:
            return self.get_accessible_time().get_end_date().strftime("%d/%m/%Y %H:%M:%S")

    def is_group_task(self):
        """ Indicates if the task submission mode is per groups """
        return self._groups

    def get_submission_limit(self):
        """ Returns the submission limits et for the task"""
        return self._submission_limit
