# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pymongo
import web
import re
from bson.objectid import ObjectId

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage
from inginious.frontend.pages.course_admin.statistics import compute_statistics
from inginious.common.base import id_checker

class CourseSubmissionViewerTaskPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET_AUTH(self, courseid, filter=""):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        
        print(course.get_id())
        print(filter)
        
        filter_item = ["username", "task"]
        filter_dict = {}

        for item in filter_item:
            filter_dict[item] = []
            s = re.search('('+item+'=([^/&])+)', filter)
            print(s)
            if s:
                s = s.group(1)
                if s:
                    s = s.replace(item+"=", "").split(",")
                    filter_dict[item] = s
                    
        print(filter_dict)
        
        if course.is_lti():
            raise web.notfound()

        return self.page(course, filter_dict)

    def submission_url_generator(self, submissionid):
        """ Generates a submission url """
        return "?submission=" + submissionid

    def page(self, course, filter_dict):
        """ Get all data and display the page """
        
        data = list(self.database.submissions.find({"username": {"$in": filter_dict["username"]},
                                                    "courseid": course.get_id(),
                                                    "taskid": {"$in": filter_dict["task"]}
                                                    }).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]
        print("----------")
        #print(data)
        print("----------")
        if "csv" in web.input():
            return make_csv(data)

        #user_task = self.database.user_tasks.find_one({"username": username, "courseid": course.get_id(), "taskid": task.get_id()})
        #submissionid = None if not user_task else user_task.get("submissionid", None)
        
        """ aggregation = self.database.aggregations.find_one({"_id": ObjectId(aggregationid)})

        # Interpret the filter and build a query
        query_tag_filter = {}
        split = str(filter).replace("/filter=", "").split(",")
        if len(split) == 2:
            tag = str(split[0])
            if id_checker(tag):
                state = (split[1] == "True" or split[1] == "true")
                query_tag_filter = {"tests." + tag: {"$in": [None, False]} if not state else True}
            

        data = list(self.database.submissions.find({"username": {"$in": aggregation["students"]},
                                                    "courseid": course.get_id(),
                                                    "taskid": task.get_id(), **query_tag_filter
                                                    },
                                                   {"text": False,
                                                    "response_type": False,
                                                    "archive": False,
                                                    "input": False}).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]

        if "csv" in web.input():
            return make_csv(data)
            
        # Get best submissions (submission for evaluation)
        # Need this for statistics computation
        # Not really optimized for now...
        user_tasks = list(self.database.user_tasks.find({"username": {"$in": aggregation["students"]}, 
                                                       "courseid": course.get_id(),
                                                       "taskid": task.get_id()},
                                                       {"submissionid": 1, "_id": 0}))
        best_submissions_list = [u["submissionid"] for u in user_tasks] # list containing ids of best submissions
        for d in data:
            d["best"] = d["_id"] in best_submissions_list # mark best submissions
            
        statistics = compute_statistics(task, data)
        
        return self.template_helper.get_renderer().course_admin.aggregation_task(course, aggregation, task, data, statistics)"""
        
        tasks = {}
        for t in filter_dict["task"]:
            tasks[t] = self.get_course_and_check_rights(course.get_id(), t)[1]
        
        return self.template_helper.get_renderer().course_admin.submission_viewer(course, tasks, filter_dict, data)
