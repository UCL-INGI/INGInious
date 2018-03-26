# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import gettext
import logging
import base64
from os import path
from bson.objectid import ObjectId
from bson.errors import InvalidId

import web

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.task_problems import DisplayableFileProblem, DisplayableMultipleChoiceProblem


class SubmissionPage(INGIniousAdminPage):
    """ List information about a task done by a student """
    _logger = logging.getLogger("inginious.frontend.submissions")

    def fetch_submission(self, submissionid):
        try:
            submission = self.submission_manager.get_submission(submissionid, False)
            if not submission:
                raise web.notfound()
        except InvalidId as ex:
            self._logger.info("Invalid ObjectId : %s", submissionid)
            raise web.notfound()

        courseid = submission["courseid"]
        taskid = submission["taskid"]
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return course, task, submission

    def GET_AUTH(self, submissionid):  # pylint: disable=arguments-differ
        """ GET request """
        course, task, submission = self.fetch_submission(submissionid)
        return self.page(course, task, submission)

    def POST_AUTH(self, submissionid):  # pylint: disable=arguments-differ
        course, task, submission = self.fetch_submission(submissionid)
        is_admin = self.user_manager.has_admin_rights_on_course(course)

        webinput = web.input()
        if "replay" in webinput and is_admin:
            self.submission_manager.replay_job(task, submission)
        elif "replay-copy" in webinput:  # Authorized for tutors
            self.submission_manager.replay_job(task, submission, True)
            web.seeother(self.app.get_homepath() + "/course/" + course.get_id() + "/" + task.get_id())
        elif "replay-debug" in webinput and is_admin:
            self.submission_manager.replay_job(task, submission, True, "ssh")
            web.seeother(self.app.get_homepath() + "/course/" + course.get_id() + "/" + task.get_id())

        return self.page(course, task, submission)

    def page(self, course, task, submission):
        """ Get all data and display the page """
        submission = self.submission_manager.get_input_from_submission(submission)
        submission = self.submission_manager.get_feedback_from_submission(
            submission,
            show_everything=True,
            translation=self.app._translations.get(self.user_manager.session_language(), gettext.NullTranslations())
        )

        to_display = []
        for problem in task.get_problems():
            if problem.get_id() in submission["input"]:  # present in input and in task
                data = {
                    "id": problem.get_id(),
                    "name": problem.get_name(self.user_manager.session_language()),
                    "defined": True,
                    "present": True,
                    "content": None,
                    "language": "plain",
                    "feedback": submission.get("problems", {}).get(problem.get_id(), None),
                    "base64": None,
                    "mime": "text/plain"
                }
                if isinstance(problem, DisplayableFileProblem):
                    extension = path.splitext(submission["input"][problem.get_id()]["filename"])[1]
                    try:
                        if extension in [".zip", ".pdf", ".tgz"]:
                            data["language"] = extension[1:]
                            data["mime"] = "application/" + extension[1:]
                        data["content"] = submission["input"][problem.get_id()]["value"].decode('utf-8')
                    except:
                        data["content"] = None
                    data["base64"] = base64.b64encode(submission["input"][problem.get_id()]["value"]).decode('utf-8')
                elif isinstance(problem, DisplayableMultipleChoiceProblem):
                    data["content"] = _("Multiple choice question:") + "\n"
                    chosen = submission["input"][problem.get_id()]
                    if not isinstance(chosen, list):
                        chosen = [chosen]
                    for c in chosen:
                        choice = problem.get_choice_with_index(int(c))
                        if choice is None:
                            t = _("unknown")
                            m = ""
                        else:
                            t = _("valid") if choice.get("valid", False) else _("invalid")
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
                    "name": problem.get_name(self.user_manager.session_language()),
                    "defined": True,
                    "present": False,
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
                        data["content"] = submission["input"][pid]["value"].decode('utf-8')
                    except:
                        data["content"] = None
                    data["base64"] = base64.b64encode(submission["input"][pid]["value"]).decode('utf-8')
                elif isinstance(submission["input"][pid], str):
                    data["content"] = submission["input"][pid]
                    data["base64"] = base64.b64encode(str(submission["input"][pid]).encode('utf-8')).decode('utf-8')
                to_display.append(data)

        return self.template_helper.get_renderer().course_admin.submission(course, task, submission, to_display)
