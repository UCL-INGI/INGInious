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
        
        filter_item = ["username", "task", "eval"]
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
        
        query = {
                "username": {"$in": filter_dict["username"]},
                "courseid": course.get_id(),
                "taskid": {"$in": filter_dict["task"]}
                }
        
        data = list(self.database.submissions.find(query).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]
        
        
        # Get best submissions (submission for evaluation)
        # Need this for statistics computation
        user_tasks = list(self.database.user_tasks.find(query, {"submissionid": 1, "_id": 0}))
        best_submissions_list = [u["submissionid"] for u in user_tasks] # list containing ids of best submissions
        for d in data:
            d["best"] = d["_id"] in best_submissions_list # mark best submissions
            
        if(filter_dict["eval"][0] == "1"):
            data = [d for d in data if d["best"]]
        
        print("----------")
        #print(data[0])
        print("----------")
        if "csv" in web.input():
            return make_csv(data)
        
        tasks = {}
        for t in filter_dict["task"]:
            tasks[t] = self.get_course_and_check_rights(course.get_id(), t)[1]
        
        return self.template_helper.get_renderer().course_admin.submission_viewer(course, tasks, filter_dict, data)
