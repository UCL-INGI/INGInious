# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pymongo
import web
from bson.objectid import ObjectId

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseAggregationTaskPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET_AUTH(self, courseid, aggregationid, taskid):  # pylint: disable=arguments-differ
        """ GET request """
        course, task = self.get_course_and_check_rights(courseid, taskid)
        return self.page(course, aggregationid, task)

    def submission_url_generator(self, submissionid):
        """ Generates a submission url """
        return "?submission=" + submissionid

    def page(self, course, aggregationid, task):
        """ Get all data and display the page """
        aggregation = self.database.aggregations.find_one({"_id": ObjectId(aggregationid)})

        data = list(self.database.submissions.find({"username": {"$in": aggregation["students"]},
                                                    "courseid": course.get_id(),
                                                    "taskid": task.get_id()},
                                                   {"text": False,
                                                    "response_type": False,
                                                    "archive": False,
                                                    "input": False}).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.aggregation_task(course, aggregation, task, data)
