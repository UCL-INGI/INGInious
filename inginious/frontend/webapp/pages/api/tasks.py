# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
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
""" Tasks """

from inginious.frontend.webapp.pages.api._api_page import APIAuthenticatedPage, APINotFound, APIForbidden
from inginious.frontend.common.parsable_text import ParsableText


class APITasks(APIAuthenticatedPage):
    r"""
        Endpoint /api/v0/courses/[a-zA-Z_\-\.0-9]+/tasks(/[a-zA-Z_\-\.0-9]+)?
    """

    def _check_for_parsable_text(self, val):
        """ Util to remove parsable text from a dict, recursively """
        if isinstance(val, ParsableText):
            return val.original_content()
        if isinstance(val, list):
            for key, val2 in enumerate(val):
                val[key] = self._check_for_parsable_text(val2)
            return val
        if isinstance(val, dict):
            for key, val2 in val.iteritems():
                val[key] = self._check_for_parsable_text(val2)
        return val

    def API_GET(self, courseid, taskid=None):
        """
            List tasks available to the connected client. Returns a dict in the form

            ::

                {
                    "taskid1":
                    {
                        "name": "Name of the course",     #the name of the course
                        "authors": [],
                        "deadline": "",
                        "status": "success"               # can be "succeeded", "failed" or "notattempted"
                        "grade": 0.0,
                        "grade_weight": 0.0,
                        "context": ""                     # context of the task, in RST
                        "problems":                       # dict of the subproblems
                        {
                                                          # see the format of task.yaml for the content of the dict. Contains everything but
                                                          # responses of multiple-choice and match problems.
                        }
                    }
                    #...
                }

            If you use the endpoint /api/v0/courses/the_course_id/tasks/the_task_id, this dict will contain one entry or the page will return 404 Not
            Found.
        """

        try:
            course = self.course_factory.get_course(courseid)
        except:
            raise APINotFound("Course not found")

        if not self.user_manager.course_is_open_to_user(course):
            raise APIForbidden("You are not registered to this course")

        if taskid is None:
            tasks = course.get_tasks()
        else:
            try:
                tasks = {taskid: course.get_task(taskid)}
            except:
                raise APINotFound("Task not found")

        output = []
        for taskid, task in tasks.iteritems():
            data = {
                "id": taskid,
                "name": task.get_name(),
                "authors": task.get_authors(),
                "deadline": task.get_deadline(),
                "status": self.user_manager.get_task_status(task),
                "grade": self.user_manager.get_task_grade(task),
                "grade_weight": task.get_grading_weight(),
                "context": task.get_context().original_content(),
                "problems": []
            }

            for problem in task.get_problems():
                pcontent = problem.get_original_content()
                pcontent["id"] = problem.get_id()
                if pcontent["type"] == "match":
                    del pcontent["answer"]
                if pcontent["type"] == "multiple-choice":
                    pcontent["choices"] = {key: val["text"] for key, val in enumerate(pcontent["choices"])}
                pcontent = self._check_for_parsable_text(pcontent)
                data["problems"].append(pcontent)

            output.append(data)

        return 200, output
