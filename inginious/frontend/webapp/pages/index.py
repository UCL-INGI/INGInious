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
""" Index page """
from collections import OrderedDict

import web

from inginious.frontend.webapp.pages.utils import INGIniousPage


class IndexPage(INGIniousPage):
    """ Index page """

    def GET(self):
        """ GET request """
        if self.user_manager.session_logged_in():
            user_input = web.input()
            if "logoff" in user_input:
                self.user_manager.disconnect_user()
                return self.call_index(False)
            else:
                return self.call_main()
        else:
            return self.call_index(False)

    def POST(self):
        """ POST request: login """
        user_input = web.input()
        if "@authid" in user_input:  # connect
            if self.user_manager.auth_user(int(user_input["@authid"]), user_input):
                return self.call_main()
            else:
                return self.call_index(True)
        elif self.user_manager.session_logged_in():  # register for a course
            return self.call_main()
        else:
            return self.call_index(False)

    def call_index(self, error):
        return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_fields(), error)

    def call_main(self):
        """ Display main page (only when logged) """

        username = self.user_manager.session_username()
        realname = self.user_manager.session_realname()
        email = self.user_manager.session_email()

        # Handle registration to a course
        user_input = web.input()
        registration_status = None
        if "register_courseid" in user_input and user_input["register_courseid"] != "":
            try:
                course = self.course_factory.get_course(user_input["register_courseid"])
                if not course.is_registration_possible(username, realname, email):
                    registration_status = False
                else:
                    registration_status = self.user_manager.course_register_user(course, username, user_input.get("register_password", None))
            except:
                registration_status = False
        if "unregister_courseid" in user_input:
            try:
                course = self.course_factory.get_course(user_input["unregister_courseid"])
                self.user_manager.course_unregister_user(course, username)
            except:
                pass

        # Display
        last_submissions = self.submission_manager.get_user_last_submissions({}, 5, True)
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = self.course_factory.get_course(submission['courseid']).get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass

        all_courses = self.course_factory.get_all_courses()

        open_courses = {courseid: course for courseid, course in all_courses.iteritems()
                        if self.user_manager.course_is_open_to_user(course, username)}
        open_courses = OrderedDict(sorted(open_courses.iteritems(), key=lambda x: x[1].get_name()))

        registerable_courses = {courseid: course for courseid, course in all_courses.iteritems() if
                                not self.user_manager.course_is_open_to_user(course, username) and
                                course.is_registration_possible(username, realname, email)}

        registerable_courses = OrderedDict(sorted(registerable_courses.iteritems(), key=lambda x: x[1].get_name()))

        return self.template_helper.get_renderer().main(open_courses, registerable_courses, except_free_last_submissions, registration_status)
