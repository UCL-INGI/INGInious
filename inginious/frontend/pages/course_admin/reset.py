# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import logging

from inginious.frontend.pages.course_admin.utils import INGIniousSubmissionAdminPage
import web

class CourseResetTaskState(INGIniousSubmissionAdminPage):
    def GET_AUTH(self, courseid,taskid):
        user_input = web.input(tasks=[], aggregations=[], users=[])
        self._logger = logging.getLogger("inginious.webapp.admin.reset")
        self.user_manager.reset_user_task_state(courseid, taskid, user_input.users[0])
        web.seeother(self.app.get_homepath() + "/admin/" + courseid + "/task/" + taskid)
