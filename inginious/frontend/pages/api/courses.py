# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Courses """

from collections import OrderedDict

from inginious.frontend.pages.api._api_page import APIAuthenticatedPage, APINotFound
from inginious.frontend.courses import WebAppCourse
from inginious.frontend.tasks import WebAppTask

class APICourses(APIAuthenticatedPage):
    r"""
        Endpoint /api/v0/courses(/[a-zA-Z_\-\.0-9]+)?
    """

    def API_GET(self, courseid=None):  # pylint: disable=arguments-differ
        """
            List courses available to the connected client. Returns a dict in the form

            ::

                {
                    "courseid1":
                    {
                        "name": "Name of the course",     #the name of the course
                        "require_password": False,        #indicates if this course requires a password or not
                        "is_registered": False,           #indicates if the user is registered to this course or not
                        "tasks":                          #only appears if is_registered is True
                        {
                            "taskid1": "name of task1",
                            "taskid2": "name of task2"
                            #...
                        },
                        "grade": 0.0                      #the current grade in the course. Only appears if is_registered is True
                    }
                    #...
                }

            If you use the endpoint /api/v0/courses/the_course_id, this dict will contain one entry or the page will return 404 Not Found.
        """
        output = []

        if courseid is None:
            courses = {course["_id"]: WebAppCourse(course["_id"], course, self.filesystem, self.plugin_manager) for course in self.database.courses.find()}
        else:
            try:
                courses = {course["_id"]: WebAppCourse(course["_id"], course, self.filesystem, self.plugin_manager) for course in self.database.courses.find({"_id": courseid})}
            except:
                raise APINotFound("Course not found")

        username = self.user_manager.session_username()
        user_info = self.database.users.find_one({"username": username})

        for courseid, course in courses.items():
            if self.user_manager.course_is_open_to_user(course, username, False) or course.is_registration_possible(user_info):
                task_descs = self.database.tasks.find({"courseid": course.get_id()}).sort("order")
                tasks = OrderedDict((task_desc["taskid"], WebAppTask(course.get_id(), task_desc["taskid"], task_desc, self.filesystem, self.plugin_manager, self.problem_types)) for task_desc in task_descs)
                data = {
                    "id": courseid,
                    "name": course.get_name(self.user_manager.session_language()),
                    "require_password": course.is_password_needed_for_registration(),
                    "is_registered": self.user_manager.course_is_open_to_user(course, username, False)
                }
                if self.user_manager.course_is_open_to_user(course, username, False):
                    data["tasks"] = {taskid: task.get_name(self.user_manager.session_language()) for taskid, task in tasks.items()}
                    data["grade"] = self.user_manager.get_course_cache(username, course, tasks)["grade"]
                output.append(data)

        return 200, output
