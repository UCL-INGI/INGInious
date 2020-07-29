# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import json
from collections import OrderedDict

import web

from inginious.common.toc import check_toc
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

class CourseTaskListPage(INGIniousAdminPage):
    """ List informations about all tasks """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        errors = []
        try:
            user_input = web.input()
            new_toc = json.loads(user_input["course_structure"])
            valid, message = check_toc(new_toc)
            if valid:
                self.course_factory.update_course_descriptor_element(courseid, 'toc', new_toc)
                course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)  # don't forget to reload the modified course
            else:
                errors.append("Invalid table of content: " + message)
        except:
            errors.append("Something wrong happened")

        return self.page(course, errors, not errors)

    def submission_url_generator(self, taskid):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&tasks=" + taskid

    def page(self, course, errors=None, validated=False):
        """ Get all data and display the page """

        # Load tasks and verify exceptions
        files = self.task_factory.get_readable_tasks(course)
        output = {}
        if errors is None:
            errors = []
        for task in files:
            try:
                output[task] = course.get_task(task)
            except Exception as inst:
                errors.append({"taskid": task, "error": str(inst)})
        tasks = OrderedDict(sorted(list(output.items()), key=lambda t: (t[1].get_order(), t[1].get_id())))

        tasks_data = OrderedDict()
        for taskid in tasks:
            tasks_data[taskid] = {"name": tasks[taskid].get_name(self.user_manager.session_language()),
                              "url": self.submission_url_generator(taskid)}
        return self.template_helper.get_renderer().course_admin.task_list(course, course.get_toc(), tasks_data, errors, validated)