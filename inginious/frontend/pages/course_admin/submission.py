# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import web
import gettext
import logging

from bson.errors import InvalidId

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


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
            self.submission_manager.replay_job(course, task, submission)
        elif "replay-copy" in webinput:  # Authorized for tutors
            self.submission_manager.replay_job(course, task, submission, True)
            web.seeother(self.app.get_homepath() + "/course/" + course.get_id() + "/" + task.get_id())
        elif "replay-debug" in webinput and is_admin:
            self.submission_manager.replay_job(course, task, submission, True, "ssh")
            web.seeother(self.app.get_homepath() + "/course/" + course.get_id() + "/" + task.get_id())

        return self.page(course, task, submission)

    def page(self, course, task, submission):
        """ Get all data and display the page """
        submission = self.submission_manager.get_input_from_submission(submission)
        submission = self.submission_manager.get_feedback_from_submission(
            submission,
            show_everything=True,
            translation=self.app.get_translation_obj()
        )

        to_display = {
            problem.get_id(): {
                "id": problem.get_id(),
                "name": problem.get_name(self.user_manager.session_language()),
                "defined": True
            } for problem in task.get_problems()
        }

        to_display.update({
            pid: {
                "id": pid,
                "name": pid,
                "defined": False
            } for pid in (set(submission["input"]) - set(to_display))
        })

        return self.template_helper.get_renderer().course_admin.submission(course, task, submission, to_display.values())
