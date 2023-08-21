# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import bson
import json
import logging
import flask
from collections import OrderedDict
from natsort import natsorted

from inginious.frontend.pages.taskset_admin.utils import INGIniousAdminPage


class TasksetTemplatePage(INGIniousAdminPage):
    """ List information about all tasks """

    def GET_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ GET request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)
        return self.page(taskset)

    def POST_AUTH(self, tasksetid):  # pylint: disable=arguments-differ
        """ POST request """
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)

        errors = []
        user_input = flask.request.form
        if "task_dispenser" in user_input:
            selected_task_dispenser = user_input.get("task_dispenser", "toc")
            task_dispenser_class = self.taskset_factory.get_task_dispensers().get(selected_task_dispenser, None)
            if task_dispenser_class:
                self.taskset_factory.update_taskset_descriptor_element(tasksetid, 'task_dispenser', task_dispenser_class.get_id())
                self.taskset_factory.update_taskset_descriptor_element(tasksetid, 'dispenser_data', {})
            else:
                errors.append(_("Invalid task dispenser"))
        elif "migrate_tasks" in user_input:
            task_dispenser = taskset.get_task_dispenser()
            try:
                data = task_dispenser.import_legacy_tasks()
                self.update_dispenser(taskset, data)
            except Exception as e:
                errors.append(_("Something wrong happened: ") + str(e))
        elif "clean_tasks" in user_input:
            try:
                self.clean_task_files(taskset)
            except Exception as e:
                errors.append(_("Something wrong happened: ") + str(e))
        else:
            try:
                self.update_dispenser(taskset, json.loads(user_input["dispenser_structure"]))
            except Exception as e:
                errors.append(_("Something wrong happened: ") + str(e))

        # don't forget to reload the modified taskset
        taskset, __ = self.get_taskset_and_check_rights(tasksetid)
        return self.page(taskset, errors, not errors)

    def update_dispenser(self, taskset, dispenser_data):
        """ Update the task dispenser based on dispenser_data """
        task_dispenser = taskset.get_task_dispenser()
        data, msg = task_dispenser.check_dispenser_data(dispenser_data)
        if data:
            self.taskset_factory.update_taskset_descriptor_element(taskset.get_id(), 'task_dispenser',
                                                                 task_dispenser.get_id())
            self.taskset_factory.update_taskset_descriptor_element(taskset.get_id(), 'dispenser_data', data)
        else:
            raise Exception(_("Invalid taskset structure: ") + msg)

    def clean_task_files(self, taskset):
        task_dispenser = taskset.get_task_dispenser()
        legacy_fields = task_dispenser.legacy_fields.keys()
        for taskid in taskset.get_tasks():
            descriptor = self.task_factory.get_task_descriptor_content(taskset.get_id(), taskid)
            for field in legacy_fields:
                descriptor.pop(field, None)
            self.task_factory.update_task_descriptor_content(taskset.get_id(), taskid, descriptor)

    def submission_url_generator(self, taskid):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&tasks=" + taskid

    def page(self, taskset, errors=None, validated=False):
        """ Get all data and display the page """

        # Load tasks and verify exceptions
        files = self.task_factory.get_readable_tasks(taskset)

        tasks = {}
        if errors is None:
            errors = []

        tasks_errors = {}
        for taskid in files:
            try:
                tasks[taskid] = taskset.get_task(taskid)
            except Exception as ex:
                tasks_errors[taskid] = str(ex)

        tasks_data = natsorted([(taskid, {"name": tasks[taskid].get_name(self.user_manager.session_language()),
                                       "url": self.submission_url_generator(taskid)}) for taskid in tasks],
                            key=lambda x: x[1]["name"])
        tasks_data = OrderedDict(tasks_data)

        task_dispensers = self.taskset_factory.get_task_dispensers()

        return self.template_helper.render("taskset_admin/template.html", taskset=taskset,
                                           task_dispensers=task_dispensers, tasks=tasks_data, errors=errors,
                                           tasks_errors=tasks_errors, validated=validated)

