# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Maintenance page """

from inginious.frontend.pages.utils import INGIniousPage


class MaintenancePage(INGIniousPage):
    """ Maintenance page """

    def GET(self):
        """ GET request """
        return self.template_helper.get_renderer(False).maintenance()

    def POST(self):
        """ POST request """
        return self.template_helper.get_renderer(False).maintenance()
