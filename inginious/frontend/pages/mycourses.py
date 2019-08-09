# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """
from collections import OrderedDict

import web

from inginious.frontend.courses import WebAppCourse
from inginious.frontend.pages.utils import INGIniousAuthPage


class MyCoursesPage(INGIniousAuthPage):
    """ Index page """

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """ Display main course list page """
        return self.show_page(None)

    def POST_AUTH(self):  # pylint: disable=arguments-differ
        """ Parse course registration or course creation and display the course list page """

        username = self.user_manager.session_username()
        user_info = self.database.users.find_one({"username": username})
        user_input = web.input()
        success = None

        # Handle registration to a course
        if "register_courseid" in user_input and user_input["register_courseid"] != "":
            try:
                course = self.database.courses.find_one({"_id": user_input["register_courseid"]})
                course = WebAppCourse(course["_id"], course, self.filesystem, self.plugin_manager)
                if not course.is_registration_possible(user_info):
                    success = False
                else:
                    success = self.user_manager.course_register_user(course, username, user_input.get("register_password", None))
            except:
                success = False
        elif "new_courseid" in user_input and self.user_manager.user_is_superadmin():
            try:
                courseid = user_input["new_courseid"]
                self.database.courses.insert({"_id": courseid, "name": courseid, "accessible": False})
                success = True
            except:
                success = False

        return self.show_page(success)

    def show_page(self, success):
        """  Display main course list page """
        username = self.user_manager.session_username()
        user_info = self.database.users.find_one({"username": username})

        all_courses = {course["_id"]: WebAppCourse(course["_id"], course, self.filesystem, self.plugin_manager) for course in self.database.courses.find()}

        # Display
        open_courses = {courseid: course for courseid, course in all_courses.items()
                        if self.user_manager.course_is_open_to_user(course, username, False) and
                        self.user_manager.course_is_user_registered(course, username)}
        open_courses = OrderedDict(sorted(iter(open_courses.items()), key=lambda x: x[1].get_name(self.user_manager.session_language())))

        last_submissions = self.submission_manager.get_user_last_submissions(5, {"courseid": {"$in": list(open_courses.keys())}})
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = open_courses[submission['courseid']].get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass

        registerable_courses = {courseid: course for courseid, course in all_courses.items() if
                                not self.user_manager.course_is_user_registered(course, username) and
                                course.is_registration_possible(user_info)}

        registerable_courses = OrderedDict(sorted(iter(registerable_courses.items()), key=lambda x: x[1].get_name(self.user_manager.session_language())))

        return self.template_helper.get_renderer().mycourses(open_courses, registerable_courses, except_free_last_submissions, success)
