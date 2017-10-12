# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Job queue status page """

from datetime import datetime

from inginious.frontend.pages.utils import INGIniousAuthPage


class QueuePage(INGIniousAuthPage):
    """ Page allowing to view the status of the backend job queue """

    def GET_AUTH(self):
        """ GET request """
        return self.template_helper.get_renderer().queue(*self.submission_manager.get_job_queue_snapshot(), datetime.fromtimestamp)
