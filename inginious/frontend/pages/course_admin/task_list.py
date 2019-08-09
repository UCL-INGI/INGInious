# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web

from inginious.frontend.tasks import WebAppTask
from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseTaskListPage(INGIniousAdminPage):
    """ List informations about all tasks """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        data = web.input(task=[])

        if "task" in data:
            # Change tasks order
            for index, taskid in enumerate(data["task"]):
                try:
                    task_desc = self.database.tasks.find_one({"courseid": courseid, "taskid": taskid})
                    task_desc["order"] = index
                    self.database.replace_one({"courseid": courseid, "taskid": taskid}, task_desc)
                except:
                    pass

        return self.page(course)

    def submission_url_generator(self, taskid):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&tasks=" + taskid

    def page(self, course):
        """ Get all data and display the page """
        data = list(self.database.user_tasks.aggregate(
            [
                {
                    "$match":
                        {
                            "courseid": course.get_id(),
                            "username": {"$in": self.user_manager.get_course_registered_users(course, False)}
                        }
                },
                {
                    "$group":
                        {
                            "_id": "$taskid",
                            "viewed": {"$sum": 1},
                            "attempted": {"$sum": {"$cond": [{"$ne": ["$tried", 0]}, 1, 0]}},
                            "attempts": {"$sum": "$tried"},
                            "succeeded": {"$sum": {"$cond": ["$succeeded", 1, 0]}}
                        }
                }
            ]))

        # Load tasks and verify exceptions
        task_descs = OrderedDict((t["taskid"], t) for t in self.database.tasks.find({"courseid": course.get_id()}).sort("order"))
        output = {}
        errors = []
        for task in task_descs:
            try:
                output[task] = WebAppTask(course.get_id(), task_descs[task]["taskid"], task_descs[task], self.filesystem,  self.plugin_manager, self.problem_types)
            except Exception as inst:
                errors.append({"taskid": task, "error": str(inst)})
        tasks = OrderedDict(sorted(list(output.items()), key=lambda t: (t[1].get_order(), t[1].get_id())))

        # Now load additional information
        result = OrderedDict()
        for taskid in tasks:
            result[taskid] = {"name": tasks[taskid].get_name(self.user_manager.session_language()), "viewed": 0, "attempted": 0, "attempts": 0, "succeeded": 0,
                              "url": self.submission_url_generator(taskid)}
        for entry in data:
            if entry["_id"] in result:
                result[entry["_id"]]["viewed"] = entry["viewed"]
                result[entry["_id"]]["attempted"] = entry["attempted"]
                result[entry["_id"]]["attempts"] = entry["attempts"]
                result[entry["_id"]]["succeeded"] = entry["succeeded"]
        if "csv" in web.input():
            return make_csv(result)

        return self.template_helper.get_renderer().course_admin.task_list(course, result, errors, self.webdav_host)
