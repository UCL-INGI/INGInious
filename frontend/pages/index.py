# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" Index page """
from collections import OrderedDict

import web

from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
from frontend.submission_manager import get_user_last_submissions
import frontend.user as User


class IndexPage(object):

    """ Index page """

    def GET(self):
        """ GET request """
        if User.is_logged_in():
            user_input = web.input()
            if "logoff" in user_input:
                User.disconnect()
                return renderer.index(False)
            else:
                return self.call_main()
        else:
            return renderer.index(False)

    def POST(self):
        """ POST request: login """
        user_input = web.input()
        if "@authid" in user_input:  # connect
            if User.connect(int(user_input["@authid"]), user_input):
                return self.call_main()
            else:
                return renderer.index(True)
        elif User.is_logged_in():  # register for a course
            return self.call_main()
        else:
            return renderer.index(False)

    def call_main(self):
        """ Display main page (only when logged) """

        # Handle registration to a course
        user_input = web.input()
        registration_status = None
        if "register_courseid" in user_input and user_input["register_courseid"] != "":
            try:
                course = FrontendCourse(user_input["register_courseid"])
                if not course.is_registration_possible():
                    registration_status = False
                else:
                    registration_status = course.register_user(User.get_username(), user_input.get("register_password", None))
            except:
                registration_status = False
        if "unregister_courseid" in user_input:
            try:
                course = FrontendCourse(user_input["unregister_courseid"])
                course.unregister_user(User.get_username())
            except:
                pass

        # Display
        last_submissions = get_user_last_submissions({}, 5)
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = FrontendCourse(submission['courseid']).get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass

        all_courses = FrontendCourse.get_all_courses()

        open_courses = {courseid: course for courseid, course in all_courses.iteritems() if course.is_open_to_user(User.get_username())}
        open_courses = OrderedDict(sorted(open_courses.iteritems(), key=lambda x: x[1].get_name()))

        registerable_courses = {courseid: course for courseid, course in all_courses.iteritems() if not course.is_open_to_user(User.get_username()) and course.is_registration_possible()}
        registerable_courses = OrderedDict(sorted(registerable_courses.iteritems(), key=lambda x: x[1].get_name()))

        return renderer.main(open_courses, registerable_courses, except_free_last_submissions, registration_status)
