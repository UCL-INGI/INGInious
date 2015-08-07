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

from collections import OrderedDict

from bson.objectid import ObjectId
import web

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.base import id_checker


class CourseDownloadSubmissions(INGIniousAdminPage):
    """ Batch operation management """

    valid_formats = formats = [
        "taskid/username",
        "taskid/classroom",
        "username/taskid",
        "classroom/taskid"
    ]

    def _validate_list(self, usernames):
        """ Prevent MongoDB injections by verifying arrays sent to it """
        for i in usernames:
            if not id_checker(i):
                raise web.notfound()

    def POST(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)

        user_input = web.input(tasks=[], classrooms=[], users=[])

        if "filter_type" not in user_input or "type" not in user_input or "format" not in user_input or user_input.format not in self.valid_formats:
            raise web.notfound()

        tasks = course.get_tasks().keys()
        for i in user_input.tasks:
            if i not in tasks:
                raise web.notfound()

        if user_input.filter_type == "users":
            self._validate_list(user_input.users)
            classrooms = list(self.database.classrooms.find({"courseid": courseid,
                                                             "students": {"$in": user_input.users}}))
        else:
            self._validate_list(user_input.classrooms)
            classrooms = list(self.database.classrooms.find({"_id": {"$in": [ObjectId(cid) for cid in user_input.classrooms]}}))

        classrooms = dict([(username, classroom) for classroom in classrooms for username in classroom["students"]])
        submissions = list(self.database.submissions.find({"username": {"$in": classrooms.keys()},
                                                           "taskid": {"$in": user_input.tasks},
                                                           "courseid": course.get_id(),
                                                           "status": {"$in": ["done", "error"]}}))
        if user_input.type == "single":
            submissions = self.submission_manager.keep_best_submission(submissions)

        web.header('Content-Type', 'application/x-gzip', unique=True)
        web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
        return self.submission_manager.get_submission_archive(submissions, list(reversed(user_input.format.split('/'))), classrooms)

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        user_input = web.input()

        # First, check for a particular submission
        if "submission" in user_input:
            submissions = list(self.database.submissions.find({"_id": ObjectId(user_input.submission),
                                                               "courseid": course.get_id(),
                                                               "status": {"$in": ["done", "error"]}}))
            if len(submissions) != 1:
                raise web.notfound()

            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
            return self.submission_manager.get_submission_archive(submissions, [], {})

        # Else, display the complete page
        tasks = {taskid: task.get_name() for taskid, task in course.get_tasks().iteritems()}

        user_list = self.user_manager.get_course_registered_users(course)
        users = OrderedDict(sorted(self.user_manager.get_users_info(user_list).items(),
                                   key=lambda k: k[1][0] if k[1] is not None else ""))
        user_data = OrderedDict([(username, user[0] if user is not None else username) for username,user in users.iteritems()])

        classrooms = self.user_manager.get_course_classrooms(course)
        classroom_data = OrderedDict([(str(classroom["_id"]), classroom["description"]) for classroom in classrooms])
        tutored_classrooms = [str(classroom["_id"]) for classroom in classrooms if self.user_manager.session_username() in classroom["tutors"]]
        tutored_users = [username for classroom in classrooms if self.user_manager.session_username() in classroom["tutors"] for username in classroom["students"]]

        checked_tasks = tasks.keys()
        checked_users = user_data.keys()
        checked_classrooms = classroom_data.keys()
        show_classrooms = False
        chosen_format = self.valid_formats[0]

        if "tasks" in user_input:
            checked_tasks = user_input.tasks.split(',')
        if "users" in user_input:
            checked_users = user_input.users.split(',')
        if "classrooms" in user_input:
            checked_classrooms = user_input.classrooms.split(',')
            show_classrooms = True
        if "tutored" in user_input:
            if user_input.tutored == "classrooms":
                checked_classrooms = tutored_classrooms
                show_classrooms = True
            elif user_input.tutored == "users":
                checked_users = tutored_users
                show_classrooms = True
        if "format" in user_input and user_input.format in self.valid_formats:
            chosen_format = user_input.format
            if "classroom" in chosen_format:
                show_classrooms = True

        return self.template_helper.get_renderer().course_admin.download(course,
                                                                         tasks, user_data, classroom_data,
                                                                         tutored_classrooms, tutored_users,
                                                                         checked_tasks, checked_users, checked_classrooms,
                                                                         self.valid_formats, chosen_format,
                                                                         show_classrooms)
