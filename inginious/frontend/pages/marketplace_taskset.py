# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """
import flask
from flask import redirect
from werkzeug.exceptions import Forbidden

from inginious.frontend.exceptions import ImportTasksetException
from inginious.frontend.marketplace_tasksets import get_marketplace_taskset
from inginious.frontend.pages.marketplace import import_taskset
from inginious.frontend.pages.utils import INGIniousAuthPage


class MarketplaceTasksetPage(INGIniousAuthPage):
    """ Course marketplace """

    def get_taskset(self, tasksetid):
        """ Return the taskset """
        try:
            taskset = get_marketplace_taskset(tasksetid)
        except:
            raise Forbidden(description=_("Taskset unavailable."))

        return taskset

    def GET_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ GET request """
        # Change to teacher privilege when created
        if not self.user_manager.user_is_superadmin():
            raise Forbidden(description=_("You're not allowed to do that"))

        taskset = self.get_taskset(tasksetid)
        return self.show_page(taskset)

    def POST_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ POST request """
        # Change to teacher privilege when created
        if not self.user_manager.user_is_superadmin():
            raise Forbidden(description=_("You're not allowed to do that"))

        taskset = self.get_taskset(tasksetid)
        user_input = flask.request.form
        errors = []
        if "new_tasksetid" in user_input:
            new_tasksetid = user_input["new_tasksetid"]
            try:
                import_taskset(taskset, new_tasksetid, self.user_manager.session_username(), self.taskset_factory)
            except ImportTasksetException as e:
                errors.append(str(e))
            if not errors:
                return redirect(self.app.get_homepath() + "/taskset/{}".format(new_tasksetid))
        return self.show_page(taskset, errors)

    def show_page(self, taskset, errors=None):
        """ Prepares and shows the taskset marketplace """
        if errors is None:
            errors = []

        return self.template_helper.render("marketplace_taskset.html", taskset=taskset, errors=errors)
