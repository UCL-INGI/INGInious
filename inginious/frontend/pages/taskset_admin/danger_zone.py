# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import glob
import logging
import os
import random
import flask
from flask import redirect, Response


from inginious.frontend.pages.taskset_admin.utils import INGIniousAdminPage
from inginious.frontend.user_manager import UserManager


class TasksetDangerZonePage(INGIniousAdminPage):
    """ Course administration page: list of audiences """
    _logger = logging.getLogger("inginious.webapp.taskset.danger_zone")

    def delete_taskset(self, tasksetid):
        """ Erase all taskset data """

        # Deletes the taskset from the factory (entire folder)
        self.taskset_factory.delete_taskset(tasksetid)

        # Removes backup
        filepath = os.path.join(self.backup_dir, tasksetid)
        if os.path.exists(os.path.dirname(filepath)):
            for backup in glob.glob(os.path.join(filepath, '*.zip')):
                os.remove(backup)

        self._logger.info("Taskset %s files erased.", tasksetid)

    def GET_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ GET request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)
        return self.page(taskset)

    def POST_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ POST request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)

        msg = ""
        error = False

        data = flask.request.form
        if not data.get("token", "") == self.user_manager.session_token():
            msg = _("Operation aborted due to invalid token.")
            error = True
        elif "deleteall" in data:
            if not data.get("tasksetid", "") == tasksetid:
                msg = _("Wrong taskset id.")
                error = True
            else:
                try:
                    if self.database.courses.find_one({"tasksetid": tasksetid}):
                        raise Exception(_("One or more course(s) rely on the current taskset."))
                    self.delete_taskset(tasksetid)
                    return redirect(self.app.get_homepath() + '/tasksets')
                except Exception as ex:
                    msg = _("An error occurred while deleting the taskset data: {}").format(str(ex))
                    error = True

        return self.page(taskset, msg, error)

    def page(self, taskset, msg="", error=False):
        """ Get all data and display the page """
        thehash = UserManager.hash_password(str(random.getrandbits(256)))
        self.user_manager.set_session_token(thehash)

        has_deployed_courses = self.database.courses.find_one({"tasksetid": taskset.get_id()}) is not None

        return self.template_helper.render("taskset_admin/danger_zone.html", taskset=taskset,
                                           has_deployed_courses=has_deployed_courses, thehash=thehash,
                                           msg=msg, error=error)
