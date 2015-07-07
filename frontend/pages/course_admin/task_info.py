# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
import web
from collections import OrderedDict
from frontend.base import get_database
from frontend.base import renderer
from frontend.pages.course_admin.utils import make_csv, get_course_and_check_rights
import frontend.user as User


class CourseTaskInfoPage(object):
    """ List informations about a task """

    def GET(self, courseid, taskid):
        """ GET request """
        course, task = get_course_and_check_rights(courseid, taskid)
        return self.page(course, task)

    def individual_submission_url_generator(self, course, task, task_data):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?dl=taskid%2Fusername&users=" + task_data + "&tasks=" + task.get_id()

    def group_submission_url_generator(self, course, task, group):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?dl=taskid%2Fgroup&groups=" + str(group['_id']) + "&tasks=" + task.get_id()

    def page(self, course, task):
        """ Get all data and display the page """
        user_list = course.get_registered_users()
        users = list(get_database().users.find({"_id": {"$in": user_list}}).sort("realname"))

        individual_results = list(get_database().user_tasks.find({"courseid": course.get_id(), "taskid": task.get_id(),
                                                  "username": {"$in": user_list}}))

        individual_data = OrderedDict([(user["_id"], {"username": user["_id"], "realname": user["realname"], "email": user["email"],
                                        "url": self.individual_submission_url_generator(course, task, user["_id"]),
                                        "tried":0, "grade": 0, "status": "notviewed"}) for user in users])

        for user in individual_results:
            individual_data[user["username"]]["tried"] = user["tried"]
            if user["tried"] == 0:
                individual_data[user["username"]]["status"] = "notattempted"
            elif user["succeeded"]:
                individual_data[user["username"]]["status"] = "succeeded"
            else:
                individual_data[user["username"]]["status"] = "failed"
            individual_data[user["username"]]["grade"] = user["grade"]

        if course.is_group_course():
            group_results = list(get_database().submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": task.get_id()
                            }
                    },
                    {
                        "$group":
                            {
                                "_id": "$groupid",
                                "tried": {"$sum": 1},
                                "succeeded": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}},
                                "grade": {"$max": "$grade"}
                            }
                    }
                ]))

            group_data = OrderedDict([(group['_id'], {"_id": group['_id'], "description": group['description'],
                                            "url": self.group_submission_url_generator(course, task, group),
                                            "tried":0, "grade": 0, "status": "notviewed",
                                            "tutors": group["tutors"]}) for group in course.get_groups()])

            for group in group_results:
                if group['_id'] is not None:
                    group_data[group["_id"]]["tried"] = group["tried"]
                    if group["tried"] == 0:
                        group_data[group["_id"]]["status"] = "notattempted"
                    elif group["succeeded"]:
                        group_data[group["_id"]]["status"] = "succeeded"
                    else:
                        group_data[group["_id"]]["status"] = "failed"
                    group_data[group["_id"]]["grade"] = group["grade"]

            my_groups, other_groups = [], []
            for group in group_data.values():
                if User.get_username() in group["tutors"]:
                    my_groups.append(group)
                else:
                    other_groups.append(group)

            if "csv" in web.input() and web.input()["csv"] == "students":
                return make_csv(individual_data.values())
            elif "csv" in web.input() and web.input()["csv"] == "groups":
                return make_csv(group_data.values())

            return renderer.course_admin.task_info(course, task, individual_data.values(), [my_groups, other_groups])

        else:

            if "csv" in web.input():
                return make_csv(individual_data.values())

            return renderer.course_admin.task_info(course, task, individual_data.values())
