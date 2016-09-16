# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" ClientTest plugin """
import logging

from inginious.frontend.webapp.pages.utils import INGIniousPage


def init(plugin_manager, _, client, _3):
    """ Init the plugin """

    class ClientTest(INGIniousPage):
        """ Returns stats about the client for distant tests """

        def GET(self):
            """ GET request """
            return str(client.get_waiting_jobs_count())

    plugin_manager.add_page("/tests/stats", ClientTest)
    logging.getLogger("inginious.webapp.plugin.ClientTest").info("Started ClientTest plugin")
