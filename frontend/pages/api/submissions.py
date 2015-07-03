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
""" Submissions """

import web

from frontend.pages.api._api_page import APIAuthenticatedPage, APINotFound, APIForbidden, APIInvalidArguments
from frontend.custom.courses import FrontendCourse
import frontend.user as User
from frontend.submission_manager import get_user_submissions, get_submission, get_input_from_submission, add_job
from common.tasks_code_boxes import FileBox
from common.tasks_problems import MultipleChoiceProblem, BasicCodeProblem


def _get_submissions(courseid, taskid, submissionid=None):
    """
        Helper for the GET methods of the two following classes
    """

    try:
        course = FrontendCourse(courseid)
    except:
        raise APINotFound("Course not found")

    if not course.is_open_to_user(User.get_username()):
        raise APIForbidden("You are not registered to this course")

    try:
        task = course.get_task(taskid)
    except:
        raise APINotFound("Task not found")

    if submissionid is None:
        submissions = get_user_submissions(task)
    else:
        try:
            submissions = [get_submission(submissionid)]
        except:
            raise APINotFound("Submission not found")
        if submissions[0]["taskid"] != task.get_id() or submissions[0]["courseid"] != course.get_id():
            raise APINotFound("Submission not found")

    output = {}

    for submission in submissions:
        data = {
            "submitted_on": str(submission["submitted_on"]),
            "status": submission["status"],
            "input": get_input_from_submission(submission, True),
            "grade": submission["grade"]
        }
        if submission["status"] == "done":
            data["result"] = submission.get("result", "crash")
            data["feedback"] = submission.get("text", "")
            data["problems_feedback"] = submission.get("problems", {})

        output[str(submission["_id"])] = data

    return 200, output


class APISubmissionSingle(APIAuthenticatedPage):
    """
        Endpoint /api/v0/courses/[a-zA-Z_\-\.0-9]+/tasks/[a-zA-Z_\-\.0-9]+/submissions/[a-zA-Z_\-\.0-9]+
    """

    def API_GET(self, courseid, taskid, submissionid):
        """
            List all the submissions that the connected user made. Returns dicts in the form

            ::

                {
                    "submission_id1":
                    {
                        "submitted_on": "date",
                        "status" : "done",          #can be "done", "waiting", "error" (execution status of the task).
                        "grade": 0.0,
                        "input": {},                #the input data. File are base64 encoded.
                        "result" : "success"        #only if status=done. Result of the execution.
                        "feedback": ""              #only if status=done. the HTML global feedback for the task
                        "problems_feedback":        #only if status=done. HTML feedback per problem. Some pid may be absent.
                        {
                            "pid1": "feedback1",
                            #...
                        }
                    }
                    #...
                }

            If you use the endpoint /api/v0/courses/the_course_id/tasks/the_task_id/submissions/submissionid,
            this dict will contain one entry or the page will return 404 Not Found.
        """
        return _get_submissions(courseid, taskid, submissionid)


class APISubmissions(APIAuthenticatedPage):
    """
        Endpoint /api/v0/courses/[a-zA-Z_\-\.0-9]+/tasks/[a-zA-Z_\-\.0-9]+/submissions
    """

    def API_GET(self, courseid, taskid):
        """
            List all the submissions that the connected user made. Returns dicts in the form

            ::

                {
                    "submission_id1":
                    {
                        "submitted_on": "date",
                        "status" : "done",          #can be "done", "waiting", "error" (execution status of the task).
                        "grade": 0.0,
                        "input": {},                #the input data. File are base64 encoded.
                        "result" : "success"        #only if status=done. Result of the execution.
                        "feedback": ""              #only if status=done. the HTML global feedback for the task
                        "problems_feedback":        #only if status=done. HTML feedback per problem. Some pid may be absent.
                        {
                            "pid1": "feedback1",
                            #...
                        }
                    }
                    #...
                }

            If you use the endpoint /api/v0/courses/the_course_id/tasks/the_task_id/submissions/submissionid,
            this dict will contain one entry or the page will return 404 Not Found.
        """
        return _get_submissions(courseid, taskid)

    def API_POST(self, courseid, taskid):
        """
            Creates a new submissions. Takes as (POST) input the key of the subproblems, with the value assigned each time.

            Returns

            - an error 400 Bad Request if all the input is not (correctly) given,
            - an error 403 Forbidden if you are not allowed to create a new submission for this task
            - an error 404 Not found if the course/task id not found
            - an error 500 Internal server error if the grader is not available,
            - 200 Ok, with {"submissionid": "the submission id"} as output.
        """

        try:
            course = FrontendCourse(courseid)
        except:
            raise APINotFound("Course not found")

        if not course.is_open_to_user(User.get_username()):
            raise APIForbidden("You are not registered to this course")

        try:
            task = course.get_task(taskid)
        except:
            raise APINotFound("Task not found")

        User.get_data().view_task(courseid, taskid)

        # Verify rights
        if not task.can_user_submit(User.get_username()):
            raise APIForbidden("Deadline reached")

        init_var = self.list_multiple_multiple_choices_and_files(task)
        user_input = task.adapt_input_for_backend(web.input(**init_var))

        if not task.input_is_consistent(user_input):
            raise APIInvalidArguments()

        # Get debug info if the current user is an admin
        debug = User.get_username() in course.get_admins()

        # Start the submission
        submissionid = add_job(task, user_input, debug)

        return 200, {"submissionid": str(submissionid)}

    def list_multiple_multiple_choices_and_files(self, task):
        """ List problems in task that expect and array as input """
        output = {}
        for problem in task.get_problems():
            if isinstance(problem, MultipleChoiceProblem) and problem.allow_multiple():
                output[problem.get_id()] = []
            elif isinstance(problem, BasicCodeProblem):
                for box in problem.get_boxes():
                    if isinstance(box, FileBox):
                        output[box.get_complete_id()] = {}
        return output
