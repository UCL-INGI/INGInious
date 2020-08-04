# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """
import web

from inginious.frontend.pages.utils import INGIniousAuthPage


class Marketplace(INGIniousAuthPage):
    """ Course marketplace """

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ POST request """
        # Change to teacher privilege when created
        if not self.user_manager.user_is_superadmin():
            raise web.notfound()
        return self.show_page()

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """
        # Change to teacher privilege when created
        if not self.user_manager.user_is_superadmin():
            raise web.notfound()
        return self.show_page()

    def show_page(self):
        """ Prepares and shows the course marketplace """
        return self.template_helper.get_renderer().marketplace()
