# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Maintenance page """

from flask.views import MethodView
from flask import current_app


class MaintenancePage(MethodView):
    """ Maintenance page """

    def get(self, path):
        """ GET request """
        return current_app.template_helper.render("maintenance.html")

    def post(self, path):
        """ POST request """
        return current_app.template_helper.render("maintenance.html")
