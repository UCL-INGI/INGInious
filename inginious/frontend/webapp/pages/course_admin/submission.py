# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import base64

import web

from os import path
from inginious.frontend.common.task_problems import DisplayableCodeFileProblem, DisplayableMultipleChoiceProblem
from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseStudentTaskSubmission(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET_AUTH(self, courseid, username, taskid, submissionid):  # pylint: disable=arguments-differ
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, username, task, submissionid)

    def POST_AUTH(self, courseid, username, taskid, submissionid):  # pylint: disable=arguments-differ
        course, task = self.get_course_and_check_rights(courseid, taskid)
        is_admin = self.user_manager.has_admin_rights_on_course(course)

        webinput = web.input()
        submission = self.submission_manager.get_submission(submissionid, False)
        if "replay" in webinput and is_admin:
            self.submission_manager.replay_job(task, submission)
        elif "replay-copy" in webinput:  # Authorized for tutors
            self.submission_manager.replay_job(task, submission, True)
            web.seeother("/course/" + courseid + "/" + taskid)
        elif "replay-debug" in webinput and is_admin:
            self.submission_manager.replay_job(task, submission, True, "ssh")
            web.seeother("/course/" + courseid + "/" + taskid)

        return self.page(course, username, task, submissionid)

    def page(self, course, username, task, submissionid):
        """ Get all data and display the page """
        submission = self.submission_manager.get_submission(submissionid, False)
        if not submission or username not in submission["username"] or submission["courseid"] != course.get_id() or submission["taskid"] != \
                task.get_id():
            raise web.notfound()
        submission = self.submission_manager.get_input_from_submission(submission)
        submission = self.submission_manager.get_feedback_from_submission(submission, show_everything=True)

        to_display = []
        for problem in task.get_problems():
            if problem.get_id() in submission["input"]:  # present in input and in task
                data = {
                    "id": problem.get_id(),
                    "name": problem.get_name(),
                    "defined": True,
                    "present": True,
                    "context": problem.get_header(),
                    "content": None,
                    "language": "plain",
                    "feedback": submission.get("problems", {}).get(problem.get_id(), None),
                    "base64": None,
                    "mime": "text/plain"
                }
                if isinstance(problem, DisplayableCodeFileProblem):
                    extension = path.splitext(submission["input"][problem.get_id()]["filename"])[1]
                    try:
                        if extension in [".zip", ".pdf", ".tgz"]:
                            data["language"] = extension[1:]
                            data["mime"] = "application/" + extension[1:]
                        data["content"] = base64.b64decode(submission["input"][problem.get_id()]["value"]).encode('utf8')
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
                    data["base64"] = base64.b64encode(str(submission["input"][problem.get_id()]).encode('utf-8')).decode('utf-8')
                elif isinstance(submission["input"][problem.get_id()], str):
                    data["content"] = submission["input"][problem.get_id()]
                    data["base64"] = base64.b64encode(str(submission["input"][problem.get_id()]).encode('utf-8')).decode('utf-8')
                    try:
                        data["language"] = problem.get_original_content()["language"]
                    except:
                        pass
                to_display.append(data)
            else:  # not present in input, but present in task
                data = {
                    "id": problem.get_id(),
                    "name": problem.get_name(),
                    "defined": True,
                    "present": False,
                    "context": problem.get_header(),
                    "content": None,
                    "language": "plain",
                    "feedback": submission.get("problems", {}).get(problem.get_id(), None),
                    "base64": None,
                    "mime": "text/plain"
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
                    "base64": None,
                    "mime": "text/plain"
                }
                if isinstance(submission["input"][pid], dict):  # file
                    extension = path.splitext(submission["input"][pid]["filename"])[1]
                    try:
                        if extension in [".zip", ".pdf", ".tgz"]:
                            data["language"] = extension[1:]
                            data["mime"] = "application/" + extension[1:]
                        data["content"] = base64.b64decode(submission["input"][pid]["value"]).decode('utf-8')
                    except:
                        data["content"] = None
                    data["base64"] = submission["input"][pid]["value"]
                elif isinstance(submission["input"][pid], str):
                    data["content"] = submission["input"][pid]
                    data["base64"] = base64.b64encode(str(submission["input"][pid]).encode('utf-8')).decode('utf-8')
                to_display.append(data)

        return self.template_helper.get_renderer().course_admin.submission(course, username, task, submissionid, submission, to_display)
