# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" JobManagerTest plugin """
from inginious.frontend.webapp.pages.utils import INGIniousPage


def init(plugin_manager, _, job_manager, _3):
    """ Init the plugin """

    class JobManagerTest(INGIniousPage):
        """ Returns stats about the job manager for distant tests """

        def GET(self):
            """ GET request """
            return str(job_manager.get_waiting_jobs_count())

    plugin_manager.add_page("/tests/stats", JobManagerTest)
    print "Started JobManagerTest plugin"
