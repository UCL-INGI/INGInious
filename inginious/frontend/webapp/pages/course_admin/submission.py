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
import base64
import web
from inginious.frontend.common.task_problems import DisplayableCodeFileProblem, DisplayableMultipleChoiceProblem

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseStudentTaskSubmission(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET(self, courseid, username, taskid, submissionid):
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, username, task, submissionid)

    def page(self, course, username, task, submissionid):
        """ Get all data and display the page """
        submission = self.submission_manager.get_submission(submissionid, False)
        if not submission or username not in submission["username"] or submission["courseid"] != course.get_id() or submission["taskid"] != \
                task.get_id():
            raise web.notfound()
        submission = self.submission_manager.get_input_from_submission(submission)
        submission = self.submission_manager.get_feedback_from_submission(submission)

        to_display = []
        for problem in task.get_problems():
            if problem.get_id() in submission["input"]: #present in input and in task
                data = {
                    "id": problem.get_id(),
                    "name": problem.get_name(),
                    "defined": True,
                    "present": True,
                    "context": problem.get_header(),
                    "content": None,
                    "language": "plain",
                    "feedback": submission.get("problems", {}).get(problem.get_id(), None),
                    "base64": None
                }
                if isinstance(problem, DisplayableCodeFileProblem):
                    try:
                        data["content"] = unicode(base64.b64decode(submission["input"][problem.get_id()]["value"]))
                    except:
                        data["content"] = None
                    data["base64"] = submission["input"][problem.get_id()]["value"]
                elif isinstance(problem, DisplayableMultipleChoiceProblem):
                    data["content"] = "Multiple choice question: \n"
                    chosen = submission["input"][problem.get_id()]
                    if not isinstance(chosen, list):
                        chosen = [chosen]
                    for c in chosen:
                        choice = problem.get_choice_with_index(int(c))
                        if choice is None:
                            t = "unknown"
                            m = ""
                        else:
                            t = "valid" if choice.get("valid", False) else "invalid"
                            m = choice["text"]
                        data["content"] += "\t- %s (%s): \n\t%s\n" % (c, t, m)
                    data["base64"] = str(base64.b64encode(str(submission["input"][problem.get_id()])))
                elif isinstance(submission["input"][problem.get_id()], basestring):
                    data["content"] = submission["input"][problem.get_id()]
                    data["base64"] = str(base64.b64encode(str(submission["input"][problem.get_id()])))
                    try:
                        data["language"]= problem.get_original_content()["language"]
                    except:
                        pass
                to_display.append(data)
            else: #not present in input, but present in task
                data = {
                    "id": problem.get_id(),
                    "name": problem.get_name(),
                    "defined": True,
                    "present": False,
                    "context": problem.get_header(),
                    "content": None,
                    "language": "plain",
                    "feedback": submission.get("problems", {}).get(problem.get_id(), None),
                    "base64": None
                }
                to_display.append(data)

        done_id = [d["id"] for d in to_display]
        for pid in submission["input"]:
            if pid not in done_id:
                data = {
                    "id": pid,
                    "name": pid,
                    "defined": False,
                    "present": True,
                    "context": None,
                    "content": None,
                    "language": "plain",
                    "feedback": submission.get("problems", {}).get(pid, None),
                    "base64": None
                }
                if isinstance(submission["input"][pid], dict): #file
                    try:
                        data["content"] = unicode(base64.b64decode(submission["input"][pid]["value"]))
                    except:
                        data["content"] = None
                    data["base64"] = submission["input"][pid]["value"]
                elif isinstance(submission["input"][pid], basestring):
                    data["content"] = submission["input"][pid]
                    data["base64"] = str(base64.b64encode(str(submission["input"][pid])))
                to_display.append(data)

        return self.template_helper.get_renderer().course_admin.submission(course, username, task, submissionid, submission, to_display)
