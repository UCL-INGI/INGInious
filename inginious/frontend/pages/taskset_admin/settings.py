# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import re
import flask

from inginious.frontend.pages.taskset_admin.utils import INGIniousAdminPage


class TasksetSettingsPage(INGIniousAdminPage):
    """ Couse settings """

    def GET_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ GET request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)
        return self.page(taskset)

    def POST_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ POST request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)

        errors = []

        data = flask.request.form

        if "delete" in data:
            taskid = data["delete"]
            try:
                self.task_factory.get_task(taskset, taskid)
            except:
                errors.append(_("Invalid taskid : {}").format(taskid))

            self.task_factory.delete_task(tasksetid, taskid)
        elif "add" in data:
            taskid = data["taskid"]
            try:
                self.task_factory.create_task(taskset, taskid, {
                    "name": taskid, "problems": {}, "environment_type": "mcq"})
            except Exception as ex:
                errors.append(_("Couldn't create task {} : ").format(taskid) + str(ex))

        else:
            taskset_content = self.taskset_factory.get_taskset_descriptor_content(tasksetid)
            taskset_content['name'] = data['name']
            if taskset_content['name'] == "":
                errors.append(_('Invalid name'))
            taskset_content['description'] = data['description']
            taskset_content['public'] = data['public'] == 'true'
            taskset_content['admins'] = list(map(str.strip, data['admins'].split(','))) if data['admins'].strip() else []
            if not self.user_manager.user_is_superadmin() and self.user_manager.session_username() not in taskset_content['admins']:
                errors.append(_('You cannot remove yourself from the administrators of this taskset'))

            if len(errors) == 0:
                self.taskset_factory.update_taskset_descriptor_content(tasksetid, taskset_content)
                taskset, __ = self.get_taskset_and_check_rights(tasksetid)  # don't forget to reload the modified taskset

        return self.page(taskset, errors, len(errors) == 0)

    def page(self, taskset, errors=[], saved=False):
        """ Get all data and display the page """
        return self.template_helper.render("taskset_admin/settings.html", taskset=taskset, errors=errors, saved=saved,
                                           webdav_host=self.webdav_host)
