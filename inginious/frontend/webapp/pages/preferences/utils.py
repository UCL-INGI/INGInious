# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import web
from inginious.frontend.webapp.pages.utils import INGIniousAuthPage


def get_menu(app, current, renderer, plugin_manager, user_manager):
    default_entries = []

    default_entries += [("profile", "<i class='fa fa-user fa-fw'></i>&nbsp; My profile"),
                        ("bindings", "<i class='fa fa-id-card-o fa-fw'></i>&nbsp; Authentication bindings")]

    if app.allow_deletion:
        default_entries += [("delete", "<i class='fa fa-user-times fa-fw'></i>&nbsp; Delete my account")]

    # Hook should return a tuple (link,name) where link is the relative link from the index of the course administration.
    additional_entries = [entry for entry in plugin_manager.call_hook('prefs_menu') if entry is not None]

    return renderer.preferences.menu(default_entries + additional_entries, current)


class RedirectPage(INGIniousAuthPage):
    """ Redirect preferences to /profile """

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ GET request """

        raise web.seeother('/preferences/profile')

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        return self.GET_AUTH()