# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseTaskInfoPage(INGIniousAdminPage):
    """ List informations about a task """

    def GET_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, task)

    def individual_submission_url_generator(self, task, task_data):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&users=" + task_data + "&tasks=" + task.get_id()

    def aggregation_submission_url_generator(self, task, aggregation):
        """ Generates a submission url """
        return "?format=taskid%2Faggregation&aggregations=" + str(aggregation['_id']) + "&tasks=" + task.get_id()

    def page(self, course, task):
        """ Get all data and display the page """
        user_list = self.user_manager.get_course_registered_users(course, False)
        users = OrderedDict(sorted(list(self.user_manager.get_users_info(user_list).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else ""))

        individual_results = list(self.database.user_tasks.find({"courseid": course.get_id(), "taskid": task.get_id(),
                                                                 "username": {"$in": user_list}}))

        individual_data = OrderedDict([(username, {"username": username, "realname": user[0] if user is not None else "",
                                                   "email": user[1] if user is not None else "",
                                                   "url": self.individual_submission_url_generator(task, username),
                                                   "tried": 0, "grade": 0, "status": "notviewed"})
                                       for username, user in users.items()])

        for user in individual_results:
            individual_data[user["username"]]["tried"] = user["tried"]
            if user["tried"] == 0:
                individual_data[user["username"]]["status"] = "notattempted"
            elif user["succeeded"]:
                individual_data[user["username"]]["status"] = "succeeded"
            else:
                individual_data[user["username"]]["status"] = "failed"
            individual_data[user["username"]]["grade"] = user["grade"]

        aggregation_data = OrderedDict()
        for aggregation in self.user_manager.get_course_aggregations(course):
            aggregation_data[aggregation['_id']] = {"_id": aggregation['_id'], "description": aggregation['description'],
                                                "url": self.aggregation_submission_url_generator(task, aggregation),
                                                "tried": 0, "grade": 0, "status": "notviewed",
                                                "tutors": aggregation["tutors"], "groups": aggregation["groups"]}

            aggregation_results = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": task.get_id(),
                                "username": {"$in": aggregation["students"]}
                            }
                    },
                    {
                        "$group":
                            {
                                "_id": "$taskid",
                                "tried": {"$sum": 1},
                                "succeeded": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}},
                                "grade": {"$max": "$grade"}
                            }
                    }
                ]))

            for g in aggregation_results:
                aggregation_data[aggregation['_id']]["tried"] = g["tried"]
                if g["tried"] == 0:
                    aggregation_data[aggregation['_id']]["status"] = "notattempted"
                elif g["succeeded"]:
                    aggregation_data[aggregation['_id']]["status"] = "succeeded"
                else:
                    aggregation_data[aggregation['_id']]["status"] = "failed"
                aggregation_data[aggregation['_id']]["grade"] = g["grade"]

        my_aggregations, other_aggregations = [], []
        for aggregation in aggregation_data.values():
            if self.user_manager.session_username() in aggregation["tutors"]:
                my_aggregations.append(aggregation)
            else:
                other_aggregations.append(aggregation)

        if "csv" in web.input() and web.input()["csv"] == "students":
            return make_csv(list(individual_data.values()))
        elif "csv" in web.input() and web.input()["csv"] == "aggregations":
            return make_csv(list(aggregation_data.values()))

        return self.template_helper.get_renderer().course_admin.task_info(course, task, individual_data.values(), [my_aggregations, other_aggregations])
