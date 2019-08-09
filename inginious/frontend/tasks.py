# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """

import gettext

from inginious.frontend.parsable_text import ParsableText
from inginious.common.base import id_checker
from inginious.common.tasks import Task
from inginious.frontend.accessible_time import AccessibleTime
from inginious.common.tags import Tag


class WebAppTask(Task):
    """ A task that stores additional context information, specific to the web app """

    def __init__(self, courseid, taskid, content, filesystem, hook_manager, task_problem_types):
        # We load the descriptor of the task here to allow plugins to modify settings of the task before it is read by the Task constructor
        if not id_checker(taskid):
            raise Exception("Task with invalid id: " + courseid + "/" + taskid)

        super(WebAppTask, self).__init__(courseid, taskid, content, filesystem, hook_manager, task_problem_types)

        self._name = self._data.get('name', 'Task {}'.format(self.get_id()))

        self._context = self._data.get('context', "")

        # Authors
        if isinstance(self._data.get('author'), str):  # verify if author is a string
            self._author = self._data['author']
        else:
            self._author = ""

        if isinstance(self._data.get('contact_url'), str):
            self._contact_url = self._data['contact_url']
        else:
            self._contact_url = ""

        # Submission storage
        self._stored_submissions = int(self._data.get("stored_submissions", 0))

        # Default download
        self._evaluate = self._data.get("evaluate", "best")

        # Grade weight
        self._weight = float(self._data.get("weight", 1.0))

        # _accessible
        self._accessible = AccessibleTime(self._data.get("accessible", None))

        # Group task
        self._groups = bool(self._data.get("groups", False))

        # Submission limits
        self._submission_limit = self._data.get("submission_limit", {"amount": -1, "period": -1})
        
        # Input random
        self._input_random = int(self._data.get("input_random", 0))
        
        # Regenerate input random
        self._regenerate_input_random = bool(self._data.get("regenerate_input_random", False))

        # Category tags
        self._categories = self._data.get("categories", [])

    def get_grading_weight(self):
        """ Get the relative weight of this task in the grading """
        return self._weight

    def get_accessible_time(self, course, plugin_override=True):
        """  Get the accessible time of this task """
        vals = self._hook_manager.call_hook('task_accessibility', course=course, task=self, default=self._accessible)
        return vals[0] if len(vals) and plugin_override else self._accessible

    def is_visible_by_students(self, course):
        """ Returns true if the task is accessible by all students that are not administrator of the course """
        return course.is_open_to_non_staff() and self.get_accessible_time(course).after_start()

    def get_deadline(self, course):
        """ Returns a string containing the deadline for this task """
        if self.get_accessible_time(course).is_always_accessible():
            return _("No deadline")
        elif self.get_accessible_time(course).is_never_accessible():
            return _("It's too late")
        else:
            # Prefer to show the soft deadline rather than the hard one
            return self.get_accessible_time(course).get_soft_end_date().strftime("%d/%m/%Y %H:%M:%S")

    def is_group_task(self):
        """ Indicates if the task submission mode is per groups """
        return self._groups

    def get_submission_limit(self):
        """ Returns the submission limits et for the task"""
        return self._submission_limit

    def get_name(self, language):
        """ Returns the name of this task """
        return self.gettext(language, self._name) if self._name else ""

    def get_context(self, course, language):
        """ Get the context(description) of this task """
        context = self.gettext(language, self._context) if self._context else ""
        vals = self._hook_manager.call_hook('task_context', course=course, task=self, default=context)
        return ParsableText(vals[0], "rst", translation=self.get_translation_obj(language)) if len(vals) \
            else ParsableText(context, "rst", translation=self.get_translation_obj(language))

    def get_authors(self, language):
        """ Return the list of this task's authors """
        return self.gettext(language, self._author) if self._author else ""

    def get_contact_url(self, _language):
        """ Return the contact link format string for this task """
        return self._contact_url or ""

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        for problem in self._problems:
            input_data = problem.adapt_input_for_backend(input_data)
        return input_data

    def get_stored_submissions(self):
        """ Indicates if only the last submission must be stored for the task """
        return self._stored_submissions

    def get_evaluate(self):
        """ Indicates the default download for the task """
        return self._evaluate

    def get_categories(self, course):
        """ Returns the tags id associated to the task """
        return [category for category in self._categories if category in course.get_tags()]
        
    def get_number_input_random(self):
        """ Return the number of random inputs """
        return self._input_random
        
    def regenerate_input_random(self):
        """ Indicates if random inputs should be regenerated """
        return self._regenerate_input_random
