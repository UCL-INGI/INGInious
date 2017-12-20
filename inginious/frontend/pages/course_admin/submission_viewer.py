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
        
        print(course.get_id())
        print(filter)
        
        filter_dict = {
            "username" : [],
            "task" : [],
            "classroom" : [],
            "eval" : ["0"],
            "show_tags" : ["0"]
            }

        for item in filter_dict:
            s = re.search('('+item+'=([^/&])+)', filter)
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
        
        #Build lists of users based on classrooms and specific users
        list_classroom_ObjectId = [ObjectId(o) for o in filter_dict["classroom"]]
        classroom = list(self.database.aggregations.find({"_id": {"$in" : list_classroom_ObjectId}}))
        students_of_classrooms = [s["students"] for s in classroom] #Extract usernames of students
        students_of_classrooms = [y for x in students_of_classrooms for y in x] #Flatten lists
        all_users = filter_dict["username"] + students_of_classrooms
        
        query = {
                "username": {"$in": all_users},
                "courseid": course.get_id(),
                "taskid": {"$in": filter_dict["task"]}
                }
        
        data = list(self.database.submissions.find(query).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]
                
        # Get best submissions (submission for evaluation)
        user_tasks = list(self.database.user_tasks.find(query, {"submissionid": 1, "_id": 0}))
        best_submissions_list = [u["submissionid"] for u in user_tasks] # list containing ids of best submissions
        for d in data:
            d["best"] = d["_id"] in best_submissions_list # mark best submissions
            
        if(filter_dict["eval"][0] == "1"):
            data = [d for d in data if d["best"]]
        
        if "csv" in web.input():
            return make_csv(data)
            
            
            
            
        users = self.get_users(course)
        
        tasks = {}
        for t in filter_dict["task"]:
            tasks[t] = self.get_course_and_check_rights(course.get_id(), t)[1]
            
        tasks = course.get_tasks();
        
        classrooms = self.user_manager.get_course_aggregations(course)
        return self.template_helper.get_renderer().course_admin.submission_viewer(course, tasks, users, classrooms, filter_dict, data)

    def get_users(self, course):
    
        users = sorted(list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items()),
            key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(list(self.user_manager.get_users_info(course.get_staff()).items()),
            key=lambda k: k[1][0] if k[1] is not None else "") + users)

        return users

        #TODO Delete code below
        """user_data = OrderedDict([(username, {
            "username": username, "realname": user[0] if user is not None else "",
            "email": user[1] if user is not None else "", "total_tasks": 0,
            "task_grades": {"answer": 0, "match": 0}, "task_succeeded": 0, "task_tried": 0, "total_tries": 0,
            "grade": 0, "url": self.submission_url_generator(username)}) for username, user in users.items()])

        for username, data in self.user_manager.get_course_caches(list(users.keys()), course).items():
            user_data[username].update(data if data is not None else {})"""