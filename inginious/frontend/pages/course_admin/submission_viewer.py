# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pymongo
import web
import re
from bson.objectid import ObjectId
from collections import OrderedDict

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage
from inginious.frontend.pages.course_admin.statistics import compute_statistics
from inginious.common.base import id_checker

class CourseSubmissionViewerTaskPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    def GET_AUTH(self, courseid, filter=""):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        
        #Dict containing all attributes we want to filter with default values
        filter_dict = {
            "username" : [],
            "task" : [],
            "classroom" : [],
            "eval" : "0", #All submissions by default
            "show_tags" : "0", #Hidden by default
            "show_id" : "0", #Hidden by default
            "grade_min" : None, #Not taken into account by default
            "grade_max" : None, #Not taken into account by default
            "sort_by" : "submitted_on",
            "order" : "0"
            }

        allowed_sort = ["submitted_on", "username", "grade", "taskid"]

        filter_dict = self.parse_query(filter, filter_dict)

        if (filter_dict["sort_by"] not in allowed_sort):
            filter_dict["sort_by"] = allowed_sort[0]

        if course.is_lti():
            raise web.notfound()

        return self.page(course, filter_dict, allowed_sort)

    def submission_url_generator(self, submissionid):
        """ Generates a submission url """
        return "?submission=" + submissionid

    def page(self, course, filter_dict, allowed_sort):
        """ Get all data and display the page """

        #Build lists of wanted users based on classrooms and specific users
        list_classroom_ObjectId = [ObjectId(o) for o in filter_dict["classroom"]]
        classroom = list(self.database.aggregations.find({"_id": {"$in" : list_classroom_ObjectId}}))
        students_of_classrooms = [s["students"] for s in classroom] #Extract usernames of students
        students_of_classrooms = [y for x in students_of_classrooms for y in x] #Flatten lists
        all_users = filter_dict["username"] + students_of_classrooms

        #Base query
        query_base = {
                "username": {"$in": all_users},
                "courseid": course.get_id(),
                "taskid": {"$in": filter_dict["task"]}
                }

        #Additional query field
        query_advanced = {}
        if (filter_dict["grade_min"] != None and filter_dict["grade_max"] == None):
            query_advanced["grade"] = {"$gte" : float(filter_dict["grade_min"])}
        elif (filter_dict["grade_min"] == None and filter_dict["grade_max"] != None):
            query_advanced["grade"] = {"$lte" : float(filter_dict["grade_max"])}
        elif (filter_dict["grade_min"] != None and filter_dict["grade_max"] != None):
            query_advanced["grade"] = {"$gte" : float(filter_dict["grade_min"]), "$lte" : float(filter_dict["grade_max"])}

        #Mongo operations
        data = list(self.database.submissions.find({**query_base, **query_advanced}).sort([(filter_dict["sort_by"], 
            pymongo.DESCENDING if filter_dict["order"] == "0" else pymongo.ASCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]

        # Get best submissions from database
        user_tasks = list(self.database.user_tasks.find(query_base, {"submissionid": 1, "_id": 0}))
        best_submissions_list = [u["submissionid"] for u in user_tasks] # list containing ids of best submissions
        for d in data:
            d["best"] = d["_id"] in best_submissions_list # mark best submissions

        #Keep best submissions
        if(filter_dict["eval"] == "1"):
            data = [d for d in data if d["best"]]

        if "csv" in web.input():
            return make_csv(data)

        users = self.get_users(course) # All users of the course
        tasks = course.get_tasks();  # All tasks of the course
        classrooms = self.user_manager.get_course_aggregations(course) # All classrooms of the course
        
        statistics = compute_statistics(tasks, data)

        return self.template_helper.get_renderer().course_admin.submission_viewer(course, tasks, users, classrooms, data, statistics, filter_dict, allowed_sort)

    def get_users(self, course):
        """ """
        users = sorted(list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items()),
            key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(list(self.user_manager.get_users_info(course.get_staff()).items()),
            key=lambda k: k[1][0] if k[1] is not None else "") + users)

        return users

            
    def parse_query(self, filter, filter_dict):
        """ """
        for item in filter_dict:
            s = re.search('('+item+'=([^/&])+)', filter)
            if s:
                s = s.group(1)
                if s:
                    s = s.replace(item+"=", "").split(",")
                    if type(filter_dict[item]) is list:
                        filter_dict[item] = s
                    elif len(s) > 0:
                            filter_dict[item] = s[0]
        return filter_dict