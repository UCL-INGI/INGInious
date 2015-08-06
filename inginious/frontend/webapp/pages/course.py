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
""" Course page """
import web

from inginious.frontend.webapp.pages.utils import INGIniousPage


class CoursePage(INGIniousPage):
    """ Course page """

    def GET(self, courseid):
        """ GET request """

        if self.user_manager.session_logged_in():
            try:
                course = self.course_factory.get_course(courseid)
                if not self.user_manager.course_is_open_to_user(course):
                    return self.template_helper.get_renderer().course_unavailable()
                else:
                    last_submissions = self.submission_manager.get_user_last_submissions_for_course(course, one_per_task=True)
                    except_free_last_submissions = []
                    for submission in last_submissions:
                        try:
                            submission["task"] = course.get_task(submission['taskid'])
                            except_free_last_submissions.append(submission)
                        except:
                            pass

                    return self.template_helper.get_renderer().course(course, except_free_last_submissions)
            except web.seeother:
                raise
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_inputs(), False)
