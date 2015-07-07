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

from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
from frontend.base import get_database
from bson.objectid import ObjectId
from bson.errors import InvalidId
import frontend.user as User

class GroupPage(object):
    """ Course page """

    def GET(self, courseid):
        """ GET request """

        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                registration_uncomplete = not course.is_open_to_user(User.get_username(), course.is_group_course())
                error = ""
                if not course.is_group_course() or User.get_username() in course.get_staff(True):
                    raise web.notfound()
                elif registration_uncomplete and not course.can_students_choose_group():
                    return renderer.course_unavailable()
                elif "register_group" in web.input():
                    try:
                        groupid = web.input()["register_group"]
                        group = get_database().groups.find_one_and_update({"_id": ObjectId(groupid),
                                                                           "course_id": courseid,
                                                                           "$where": "this.users.length < this.size"},
                                                                          {"$push": {"users": User.get_username()}})
                        if group:
                            raise web.seeother("/course/" + courseid)
                        else:
                            error = "Couldn't register to the specified group."
                    except InvalidId:
                        error = "Couldn't register to the specified group."

                last_submissions = course.get_user_last_submissions(one_per_task=True)
                except_free_last_submissions = []
                for submission in last_submissions:
                    try:
                        submission["task"] = course.get_task(submission['taskid'])
                        except_free_last_submissions.append(submission)
                    except:
                        pass

                group = course.get_user_group(User.get_username())
                available_groups = list(get_database().groups.find({"course_id": courseid,
                                                               "$where": "this.users.length < this.size"}))

                users = {}
                for user in get_database().users.find({"_id": {"$in": course.get_registered_users(True)}}):
                    users[user["_id"]] = user

                return renderer.group(course, except_free_last_submissions, group, available_groups, users, error)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)