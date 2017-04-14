# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

from bson.objectid import ObjectId
import inginious.common.custom_yaml as yaml
import web

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseAggregationListPage(INGIniousAdminPage):
    """ Course administration page: list of aggregations """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="aggregations.yaml"', unique=True)
            if course.use_classrooms():
                aggregations = [{"default": aggregation["default"],
                               "description": aggregation["description"],
                               "groups": aggregation["groups"],
                               "students": aggregation["students"],
                               "tutors": aggregation["tutors"]} for aggregation in
                              self.user_manager.get_course_aggregations(course)]
            else:
                aggregations = [{"default": aggregation["default"],
                               "description": aggregation["description"],
                               "groups": aggregation["groups"],
                               "students": aggregation["students"],
                               "tutors": aggregation["tutors"]} for aggregation in
                              self.user_manager.get_course_aggregations(course) if len(aggregation["groups"]) > 0]

            return yaml.dump(aggregations)

        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, _ = self.get_course_and_check_rights(courseid)

        error = False
        try:
            if self.user_manager.has_admin_rights_on_course(course):
                data = web.input()
                if 'classroom' in data:
                    default = True if self.database.aggregations.find_one({"courseid": courseid, "default": True}) is None else False
                    self.database.aggregations.insert({"default": default, "courseid": courseid, "students": [],
                                                     "tutors": [], "groups": [],
                                                     "description": data['classroom']})
                    msg = "New classroom created."
                elif 'default' in data:
                    self.database.aggregations.find_one_and_update({"courseid": courseid, "default": True},
                                                                 {"$set": {"default": False}})
                    self.database.aggregations.find_one_and_update({"_id": ObjectId(data['default'])},
                                                                 {"$set": {"default": True}})
                    msg = "Default classroom changed."
                else:  # default, but with no classroom detected
                    msg = "Invalid classroom selected."
            else:
                msg = "You have no rights to add/change classrooms"
                error = True
        except:
            msg = 'User returned an invalid form.'
            error = True

        return self.page(course, msg, error)

    def submission_url_generator(self, aggregationid):
        """ Generates a submission url """
        return "?format=taskid%2Faggregation&aggregations=" + str(aggregationid)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        aggregations = OrderedDict()
        taskids = list(course.get_tasks().keys())

        for aggregation in self.user_manager.get_course_aggregations(course):
            aggregations[aggregation['_id']] = dict(list(aggregation.items()) +
                                                [("tried", 0),
                                                 ("done", 0),
                                                 ("url", self.submission_url_generator(aggregation['_id']))
                                                 ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": taskids},
                                "username": {"$in": aggregation["students"]}
                            }
                    },
                    {
                        "$group":
                            {
                                "_id": "$taskid",
                                "tried": {"$sum": 1},
                                "done": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}}
                            }
                    },

                ]))

            for c in data:
                aggregations[aggregation['_id']]["tried"] += 1 if c["tried"] else 0
                aggregations[aggregation['_id']]["done"] += 1 if c["done"] else 0

        my_aggregations, other_aggregations = [], []
        for aggregation in aggregations.values():
            if self.user_manager.session_username() in aggregation["tutors"]:
                my_aggregations.append(aggregation)
            else:
                other_aggregations.append(aggregation)

        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.aggregation_list(course, [my_aggregations, other_aggregations], msg, error)
