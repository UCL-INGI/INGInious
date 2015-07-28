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

import web
from bson.objectid import ObjectId
from bson.errors import InvalidId

from frontend.webapp.pages.utils import INGIniousPage


class GroupPage(INGIniousPage):
    """ Course page """

    def GET(self, courseid):
        """ GET request """

        if self.user_manager.session_logged_in():
            try:
                course = self.course_factory.get_course(courseid)
                registration_uncomplete = not self.user_manager.course_is_open_to_user(course)
                error = ""
                if not course.is_group_course() or self.user_manager.has_staff_rights_on_course(course):
                    raise web.notfound()
                elif registration_uncomplete and not course.can_students_choose_group():
                    return self.template_helper.get_renderer().course_unavailable()
                elif "register_group" in web.input():
                    try:
                        groupid = web.input()["register_group"]
                        group = self.database.groups.find_one_and_update({"_id": ObjectId(groupid),
                                                                          "course_id": courseid,
                                                                          "$where": "this.users.length < this.size"},
                                                                         {"$push": {"users": self.user_manager.session_username()}})
                        if group:
                            raise web.seeother("/course/" + courseid)
                        else:
                            error = "Couldn't register to the specified group."
                    except InvalidId:
                        error = "Couldn't register to the specified group."

                last_submissions = self.submission_manager.get_user_last_submissions_for_course(course, one_per_task=True)
                except_free_last_submissions = []
                for submission in last_submissions:
                    try:
                        submission["task"] = course.get_task(submission['taskid'])
                        except_free_last_submissions.append(submission)
                    except:
                        pass

                group = self.user_manager.get_course_user_group(course)
                available_groups = list(self.database.groups.find({"course_id": courseid,
                                                                   "$where": "this.users.length < this.size"}))

                users = {}
                for username, user in self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course)).iteritems():
                    users[username] = {"realname": user[0], "email": user[1]}

                return self.template_helper.get_renderer().group(course, except_free_last_submissions, group, available_groups, users, error)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_inputs(), False)
