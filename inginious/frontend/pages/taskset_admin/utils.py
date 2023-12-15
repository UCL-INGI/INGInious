# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for administration pages """

from collections import OrderedDict
from datetime import datetime

from flask import redirect, Response
from werkzeug.exceptions import Forbidden

from inginious.common.base import id_checker
from inginious.frontend.pages.utils import INGIniousAuthPage


class INGIniousAdminPage(INGIniousAuthPage):
    """
    An improved version of INGIniousAuthPage that checks rights for the administration
    """

    def get_taskset_and_check_rights(self, tasksetid, taskid=None):
        """ Returns the course with id ``courseid`` and the task with id ``taskid``, and verify the rights of the user.
            Raise app.forbidden() when there is no such course of if the users has not enough rights.
            :param courseid: the course on which to check rights
            :param taskid: If not None, returns also the task with id ``taskid``
            :returns (Course, Task)
        """

        try:
            taskset = self.taskset_factory.get_taskset(tasksetid)
            if not self.user_manager.session_username() in taskset.get_admins() and not self.user_manager.user_is_superadmin():
                raise Forbidden(description=_("You don't have admin rights on this taskset."))

            if taskid is None:
                return taskset, None
            else:
                return taskset, taskset.get_task(taskid)
        except Forbidden as f:
            raise
        except:
            raise Forbidden(description=_("This taskset is unreachable"))


class TasksetRedirectPage(INGIniousAdminPage):
    """ Redirect to /settings """

    def GET_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ GET request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)
        return redirect(self.app.get_homepath() + '/taskset/{}/settings'.format(tasksetid))

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        return self.GET_AUTH(courseid)


def get_menu(taskset, current, renderer, user_manager):
    """ Returns the HTML of the menu used in the administration. ```current``` is the current page of section """
    default_entries = [("settings", "<i class='fa fa-cog fa-fw'></i>&nbsp; " + _("Settings")),
                       ("template", "<i class='fa fa-file-o fa-fw'></i>&nbsp; " + _("Course template")),
                       ("danger", "<i class='fa fa-bomb fa-fw'></i>&nbsp; " + _("Danger zone"))]

    return renderer("taskset_admin/menu.html", taskset=taskset, entries=default_entries, current=current)