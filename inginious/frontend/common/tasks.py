# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """
from inginious.common.base import id_checker
import inginious.common.tasks
from inginious.frontend.common.parsable_text import ParsableText
from inginious.frontend.common.task_problems import DisplayableCodeProblem, DisplayableCodeFileProblem, DisplayableCodeSingleLineProblem, \
    DisplayableMultipleChoiceProblem, DisplayableMatchProblem, DisplayableCodeMultipleLanguagesProblem, DisplayableCodeFileMultipleLanguagesProblem 


class FrontendTask(inginious.common.tasks.Task):
    """ A task that stores additional context information """

    def __init__(self, course, taskid, content, directory_path, hook_manager, task_problem_types=None):
        # We load the descriptor of the task here to allow plugins to modify settings of the task before it is read by the Task constructor
        if not id_checker(taskid):
            raise Exception("Task with invalid id: " + course.get_id() + "/" + taskid)

        task_problem_types = task_problem_types or {
            "code": DisplayableCodeProblem,
            "code-multiple-languages": DisplayableCodeMultipleLanguagesProblem,
            "code-file": DisplayableCodeFileProblem,
            "code-file-multiple-languages": DisplayableCodeFileMultipleLanguagesProblem,
            "code-single-line": DisplayableCodeSingleLineProblem,
            "multiple-choice": DisplayableMultipleChoiceProblem,
            "match": DisplayableMatchProblem}

        super(FrontendTask, self).__init__(course, taskid, content, directory_path, hook_manager, task_problem_types)

        self._name = self._data.get('name', 'Task {}'.format(self.get_id()))

        self._context = ParsableText(self._data.get('context', ""), "rst")

        # Authors
        if isinstance(self._data.get('author'), str):  # verify if author is a string
            self._author = [self._data['author']]
        elif isinstance(self._data.get('author'), list):  # verify if author is a list
            for author in self._data['author']:
                if not isinstance(author, str):  # authors must be strings
                    raise Exception("This task has an invalid author")
            self._author = self._data['author']
        else:
            self._author = []

        # Submission storage
        self._stored_submissions = int(self._data.get("stored_submissions", 0))

        # Default download
        self._evaluate = self._data.get("evaluate", "best")

    def get_name(self):
        """ Returns the name of this task """
        return self._name

    def get_context(self):
        """ Get the context(description) of this task """
        vals = self._hook_manager.call_hook('task_context', course=self.get_course(), task=self, default=self._context)
        return vals[0] if len(vals) else self._context

    def get_authors(self):
        """ Return the list of this task's authors """
        return self._author

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
