# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Main page for the LTI provider. Displays a task and allow to answer to it. """
import web

from inginious.frontend.lti.pages.utils import LTILaunchPage


class LTILaunchTask(LTILaunchPage):
    def LAUNCH_POST(self):
        raise web.seeother('/' + self.user_manager.get_session_identifier() + '/task')
