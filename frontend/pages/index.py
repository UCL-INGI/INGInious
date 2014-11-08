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
        if "@authid" in user_input and User.connect(int(user_input["@authid"]), user_input):
            return self.call_main()
        else:
            return renderer.index(True)

    def call_main(self):
        """ Display main page (only when logged) """
        last_submissions = get_user_last_submissions({}, 5)
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = FrontendCourse(submission['courseid']).get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass
        courses = {courseid: course for courseid, course in FrontendCourse.get_all_courses().iteritems() if course.is_open_to_user(User.get_username())}
        courses = OrderedDict(sorted(courses.iteritems(), key=lambda x: x[1].get_name()))
        return renderer.main(courses, except_free_last_submissions)
