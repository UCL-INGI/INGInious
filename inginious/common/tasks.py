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
""" Task """
from inginious.common.base import id_checker
from inginious.common.tasks_problems import CodeProblem, CodeSingleLineProblem, MultipleChoiceProblem, MatchProblem, CodeFileProblem


class Task(object):
    """ Contains the data for a task """

    def __init__(self, course, taskid, content, directory_path, task_problem_types=None):
        """
            Init the task. course is a Course object, taskid the task id, and content is a dictionnary containing the data needed to initialize the Task object.
            If init_data is None, the data will be taken from the course tasks' directory.
        """
        self._course = course
        self._taskid = taskid
        self._directory_path = directory_path

        task_problem_types = task_problem_types or {"code": CodeProblem, "code-single-line": CodeSingleLineProblem, "code-file": CodeFileProblem,
                                                    "multiple-choice": MultipleChoiceProblem, "match": MatchProblem}

        self._data = content

        self._environment = self._data.get('environment', None)

        # Response is HTML
        self._response_is_html = self._data.get("responseIsHTML", False)

        # Limits
        self._limits = {"time": 20, "memory": 1024, "disk": 1024}
        if "limits" in self._data:
            try:
                self._limits['time'] = int(self._data["limits"].get("time", 20))
                self._limits['hard_time'] = int(3 * self._data["limits"].get("hard_time", 60))
                self._limits['memory'] = int(self._data["limits"].get("memory", 1024))
                self._limits['disk'] = int(self._data["limits"].get("disk", 1024))

                if self._limits['time'] <= 0 or self._limits['hard_time'] <= 0 or self._limits['memory'] <= 0 or self._limits['disk'] <= 0:
                    raise Exception("Invalid limit")
            except:
                raise Exception("Invalid limit")

        if "problems" not in self._data:
            raise Exception("Tasks must have some problems descriptions")

        # Check all problems
        self._problems = []

        for problemid in self._data['problems']:
            self._problems.append(self._create_task_problem(problemid, self._data['problems'][problemid], task_problem_types))

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):
        """ Check if an input for a task is consistent. Return true if this is case, false else """
        for problem in self._problems:
            if not problem.input_is_consistent(task_input, default_allowed_extension, default_max_size):
                return False
        return True

    def get_environment(self):
        """ Returns the environment in which the job manager have to launch this task"""
        return self._environment

    def get_id(self):
        """ Get the id of this task """
        return self._taskid

    def get_problems(self):
        """ Get problems contained in this task """
        return self._problems

    def get_course_id(self):
        """ Return the courseid of the course that contains this task """
        return self._course.get_id()

    def get_course(self):
        """ Return the course that contains this task """
        return self._course

    def get_limits(self):
        """ Return the limits of this task """
        return self._limits

    def get_response_type(self):
        """ Returns the method used to parse the output of the task: HTML or rst """
        return "HTML" if self._response_is_html else "rst"

    def get_directory_path(self):
        """ Returns the path to the directory containing the files related to the task """
        return self._directory_path

    def check_answer(self, task_input):
        """
            Verify the answers in task_input. Returns five values
            1st: True the input is **currently** valid. (may become invalid after running the code), False else
            2nd: True if the input needs to be run in the VM, False else
            3rd: Main message, as a list (that can be join with \n or <br/> for example)
            4th: Problem specific message, as a dictionnary
            5th: Number of errors in the multiple choices
        """
        valid = True
        need_launch = False
        main_message = []
        problem_messages = {}
        multiple_choice_error_count = 0
        for problem in self._problems:
            problem_is_valid, problem_main_message, problem_s_messages, problem_mc_error_count = problem.check_answer(task_input)
            if problem_is_valid is None:
                need_launch = True
            elif problem_is_valid == False:
                valid = False
            if problem_main_message is not None:
                main_message.append(problem_main_message)
            if problem_s_messages is not None:
                problem_messages[problem.get_id()] = problem_s_messages
            multiple_choice_error_count += problem_mc_error_count
        return valid, need_launch, main_message, problem_messages, multiple_choice_error_count

    def _create_task_problem(self, problemid, problem_content, task_problem_types):
        """Creates a new instance of the right class for a given problem."""
        # Basic checks
        if not id_checker(problemid):
            raise Exception("Invalid problem _id: " + problemid)
        if problem_content.get('type', "") not in task_problem_types:
            raise Exception("Invalid type for problem " + problemid)

        return task_problem_types.get(problem_content.get('type', ""))(self, problemid, problem_content)
