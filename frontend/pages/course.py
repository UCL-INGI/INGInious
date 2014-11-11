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
""" Course page """
import web

from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
import frontend.user as User
# Course page


class CoursePage(object):

    """ Course page """

    def GET(self, courseid):
        """ GET request """

        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if not course.is_open_to_user(User.get_username()):
                    return renderer.course_unavailable()

                last_submissions = course.get_user_last_submissions()
                except_free_last_submissions = []
                for submission in last_submissions:
                    try:
                        submission["task"] = course.get_task(submission['taskid'])
                        except_free_last_submissions.append(submission)
                    except:
                        pass
                return renderer.course(course, except_free_last_submissions)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
