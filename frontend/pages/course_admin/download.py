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

from frontend.base import renderer
from frontend.pages.course_admin.utils import get_course_and_check_rights
from frontend.base import get_database
import frontend.user as User
from collections import OrderedDict
from frontend.submission_manager import get_submission_archive, keep_best_submission
from bson.objectid import ObjectId
from common.base import id_checker
import web

class CourseDownloadSubmissions(object):
    """ Batch operation management """

    valid_formats = formats = [
        "taskid/username",
        "taskid/group",
        "username/taskid",
        "group/taskid"
    ]

    def _validate_list(self, usernames):
        """ Prevent MongoDB injections by verifying arrays sent to it """
        for i in usernames:
            if not id_checker(i):
                raise web.notfound()

    def POST(self, courseid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)

        user_input = web.input(tasks=[], groups=[], users=[])

        if "filter_type" not in user_input or "type" not in user_input or "format" not in user_input or user_input.format not in self.valid_formats:
            raise web.notfound()

        tasks = course.get_tasks().keys()
        for i in user_input.tasks:
            if i not in tasks:
                raise web.notfound()

        if user_input.filter_type == "users":
            self._validate_list(user_input.users)
            submissions = list(get_database().submissions.find({"username": {"$in": user_input.users},
                                                                "taskid": {"$in": user_input.tasks},
                                                                "courseid": course.get_id(),
                                                                "status": {"$in": ["done", "error"]}}))
        else:
            self._validate_list(user_input.groups)
            submissions = list(get_database().submissions.find({"groupid": {"$in": [ObjectId(gid) for gid in user_input.groups]},
                                                                "taskid": {"$in": user_input.tasks},
                                                                "courseid": course.get_id(),
                                                                "status": {"$in": ["done", "error"]}}))
        if user_input.type == "single":
            submissions = keep_best_submission(submissions)

        web.header('Content-Type', 'application/x-gzip', unique=True)
        web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
        return get_submission_archive(submissions, list(reversed(user_input.format.split('/'))))

    def GET(self, courseid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)
        user_input = web.input()

        # First, check for a particular submission
        if "submission" in user_input:
            submissions = list(get_database().submissions.find({"_id": ObjectId(user_input.submission),
                                                                "courseid": course.get_id(),
                                                                "status": {"$in": ["done", "error"]}}))
            if len(submissions) != 1:
                raise web.notfound()

            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
            return get_submission_archive(submissions, [])

        # Else, display the complete page
        tasks = {taskid: task.get_name() for taskid, task in course.get_tasks().iteritems()}

        user_list = course.get_registered_users()
        users = list(get_database().users.find({"_id": {"$in": user_list}}).sort("realname"))
        user_data = OrderedDict([(user["_id"], user["realname"]) for user in users])

        groups = course.get_groups()
        group_data = OrderedDict([(group["_id"], group["description"]) for group in groups])
        tutored_groups = [group["_id"] for group in groups if User.get_username() in group["tutors"]]
        tutored_users = [username for group in groups if User.get_username() in group["tutors"] for username in group["users"]]

        checked_tasks = tasks.keys()
        checked_users = user_data.keys()
        checked_groups = group_data.keys()
        show_groups = False
        chosen_format = self.valid_formats[0]

        if "tasks" in user_input:
            checked_tasks = user_input.tasks.split(',')
        if "users" in user_input:
            checked_users = user_input.users.split(',')
        if "groups" in user_input:
            checked_groups = user_input.groups.split(',')
            show_groups = True
        if "tutored" in user_input:
            if user_input.tutored == "groups":
                checked_groups = tutored_groups
                show_groups = True
            elif user_input.tutored == "users":
                checked_users = tutored_users
                show_groups = True
        if "format" in user_input and user_input.format in self.valid_formats:
            chosen_format = user_input.format
            if "group" in chosen_format:
                show_groups = True

        return renderer.course_admin.download(course,
                                              tasks, user_data, group_data,
                                              tutored_groups, tutored_users,
                                              checked_tasks, checked_users, checked_groups,
                                              self.valid_formats, chosen_format,
                                              show_groups)