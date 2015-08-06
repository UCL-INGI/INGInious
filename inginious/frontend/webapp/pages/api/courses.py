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
""" Courses """

from inginious.frontend.webapp.pages.api._api_page import APIAuthenticatedPage, APINotFound


class APICourses(APIAuthenticatedPage):
    r"""
        Endpoint /api/v0/courses(/[a-zA-Z_\-\.0-9]+)?
    """

    def API_GET(self, courseid=None):
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
            courses = self.course_factory.get_all_courses()
        else:
            try:
                courses = {courseid: self.course_factory.get_course(courseid)}
            except:
                raise APINotFound("Course not found")

        username = self.user_manager.session_username()
        realname = self.user_manager.session_realname()
        email = self.user_manager.session_email()

        for courseid, course in courses.iteritems():
            if self.user_manager.course_is_open_to_user(course, username) or course.is_registration_possible(username, realname, email):
                data = {
                    "id": courseid,
                    "name": course.get_name(),
                    "require_password": course.is_password_needed_for_registration(),
                    "is_registered": self.user_manager.course_is_open_to_user(course, username)
                }
                if self.user_manager.course_is_open_to_user(course, username):
                    data["tasks"] = {taskid: task.get_name() for taskid, task in course.get_tasks().iteritems()}
                    data["grade"] = self.user_manager.get_course_grade(course)
                output.append(data)

        return 200, output
