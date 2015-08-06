# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Classes modifying basic tasks, problems and boxes classes """
from inginious.common.base import id_checker
import inginious.common.tasks
from inginious.frontend.common.parsable_text import ParsableText
from inginious.frontend.common.task_problems import DisplayableCodeProblem, DisplayableCodeFileProblem, DisplayableCodeSingleLineProblem, \
    DisplayableMultipleChoiceProblem, DisplayableMatchProblem


class FrontendTask(inginious.common.tasks.Task):
    """ A task that stores additional context information """

    def __init__(self, course, taskid, content, directory_path, task_problem_types=None):
        # We load the descriptor of the task here to allow plugins to modify settings of the task before it is read by the Task constructor
        if not id_checker(taskid):
            raise Exception("Task with invalid id: " + course.get_id() + "/" + taskid)

        task_problem_types = task_problem_types or {
            "code": DisplayableCodeProblem,
            "code-file": DisplayableCodeFileProblem,
            "code-single-line": DisplayableCodeSingleLineProblem,
            "multiple-choice": DisplayableMultipleChoiceProblem,
            "match": DisplayableMatchProblem}

        super(FrontendTask, self).__init__(course, taskid, content, directory_path, task_problem_types)

        self._name = self._data.get('name', 'Task {}'.format(self.get_id()))

        self._context = ParsableText(self._data.get('context', ""), "rst")

        # Authors
        if isinstance(self._data.get('author'), basestring):  # verify if author is a string
            self._author = [self._data['author']]
        elif isinstance(self._data.get('author'), list):  # verify if author is a list
            for author in self._data['author']:
                if not isinstance(author, basestring):  # authors must be strings
                    raise Exception("This task has an invalid author")
            self._author = self._data['author']
        else:
            self._author = []

    def get_name(self):
        """ Returns the name of this task """
        return self._name

    def get_context(self):
        """ Get the context(description) of this task """
        return self._context

    def get_authors(self):
        """ Return the list of this task's authors """
        return self._author

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        for problem in self._problems:
            input_data = problem.adapt_input_for_backend(input_data)
        return input_data
