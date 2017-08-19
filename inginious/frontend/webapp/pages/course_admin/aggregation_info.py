# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import web
from bson.objectid import ObjectId

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseAggregationInfoPage(INGIniousAdminPage):
    """ List information about a aggregation """

    def GET_AUTH(self, courseid, aggregationid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)

        if course.is_lti():
            raise web.notfound()

        return self.page(course, aggregationid)

    def submission_url_generator(self, aggregationid, taskid):
        """ Generates a submission url """
        return "?format=taskid%2Faggregation&tasks=" + taskid + "&aggregations=" + str(aggregationid)

    def page(self, course, aggregationid):
        """ Get all data and display the page """
        aggregation = self.database.aggregations.find_one({"_id": ObjectId(aggregationid)})

        data = list(self.database.submissions.aggregate(
            [
                {
                    "$match":
                        {
                            "courseid": course.get_id(),
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

        tasks = course.get_tasks()
        result = dict([(taskid, {"taskid": taskid, "name": tasks[taskid].get_name(), "tried": 0, "status": "notviewed",
                                 "grade": 0, "url": self.submission_url_generator(aggregationid, taskid)}) for taskid in tasks])

        for taskdata in data:
            if taskdata["_id"] in result:
                result[taskdata["_id"]]["tried"] = taskdata["tried"]
                if taskdata["tried"] == 0:
                    result[taskdata["_id"]]["status"] = "notattempted"
                elif taskdata["succeeded"]:
                    result[taskdata["_id"]]["status"] = "succeeded"
                else:
                    result[taskdata["_id"]]["status"] = "failed"
                result[taskdata["_id"]]["grade"] = taskdata["grade"]

        if "csv" in web.input():
            return make_csv(result)

        results = sorted(list(result.values()), key=lambda result: (tasks[result["taskid"]].get_order(), result["taskid"]))
        return self.template_helper.get_renderer().course_admin.aggregation_info(course, aggregation, results)
