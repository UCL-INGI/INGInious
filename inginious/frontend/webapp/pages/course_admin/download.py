# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


from collections import OrderedDict

from bson.objectid import ObjectId
import web

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.base import id_checker


class CourseDownloadSubmissions(INGIniousAdminPage):
    """ Batch operation management """

    def valid_formats(self, course):
        return [
            "taskid/username",
            "taskid/aggregation",
            "username/taskid",
            "aggregation/taskid"
        ]

    def _validate_list(self, usernames):
        """ Prevent MongoDB injections by verifying arrays sent to it """
        for i in usernames:
            if not id_checker(i):
                raise web.notfound()

    def POST(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)

        user_input = web.input(tasks=[], aggregations=[], users=[])

        if "filter_type" not in user_input or "type" not in user_input or "format" not in user_input or user_input.format not in self.valid_formats(course):
            raise web.notfound()

        tasks = list(course.get_tasks().keys())
        for i in user_input.tasks:
            if i not in tasks:
                raise web.notfound()

        if user_input.filter_type == "users":
            self._validate_list(user_input.users)
            aggregations = list(self.database.aggregations.find({"courseid": courseid,
                                                             "students": {"$in": user_input.users}}))
        else:
            self._validate_list(user_input.aggregations)
            aggregations = list(self.database.aggregations.find({"_id": {"$in": [ObjectId(cid) for cid in user_input.aggregations]}}))

        # Tweak if not using classrooms : classroom['students'] may content ungrouped users
        aggregations = dict([(username,
                              aggregation if course.use_classrooms() or (username in aggregation['groups'][0]["students"]) else None
                              ) for aggregation in aggregations for username in aggregation["students"]])

        if user_input.type == "single":
            user_tasks = list(self.database.user_tasks.find({"username": {"$in": list(aggregations.keys())},
                                                        "taskid": {"$in": user_input.tasks},
                                                        "courseid": course.get_id()}))

            submissionsid = [user_task['submissionid'] for user_task in user_tasks]
            submissions = list(self.database.submissions.find({"_id": {"$in": submissionsid}}))
        else:
            submissions = list(self.database.submissions.find({"username": {"$in": list(aggregations.keys())},
                                                               "taskid": {"$in": user_input.tasks},
                                                               "courseid": course.get_id(),
                                                               "status": {"$in": ["done", "error"]}}))

        web.header('Content-Type', 'application/x-gzip', unique=True)
        web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
        return self.submission_manager.get_submission_archive(submissions, list(reversed(user_input.format.split('/'))), aggregations)

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
        tasks = {taskid: task.get_name() for taskid, task in course.get_tasks().items()}

        user_list = self.user_manager.get_course_registered_users(course, False)
        users = OrderedDict(sorted(list(self.user_manager.get_users_info(user_list).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else ""))
        user_data = OrderedDict([(username, user[0] if user is not None else username) for username, user in users.items()])

        aggregations = self.user_manager.get_course_aggregations(course)
        tutored_aggregations = [str(aggregation["_id"]) for aggregation in aggregations if self.user_manager.session_username() in aggregation["tutors"] and len(aggregation['groups']) > 0]

        tutored_users = []
        for aggregation in aggregations:
            for username in aggregation["students"]:
                # If no classrooms used, only students inside groups
                if self.user_manager.session_username() in aggregation["tutors"] and \
                        (course.use_classrooms() or
                             (len(aggregation['groups']) > 0 and username in aggregation['groups'][0]['students'])):
                    tutored_users += [username]

        checked_tasks = list(tasks.keys())
        checked_users = list(user_data.keys())
        checked_aggregations = [aggregation['_id'] for aggregation in aggregations]
        show_aggregations = False
        chosen_format = self.valid_formats(course)[0]

        if "tasks" in user_input:
            checked_tasks = user_input.tasks.split(',')
        if "users" in user_input:
            checked_users = user_input.users.split(',')
        if "aggregations" in user_input:
            checked_aggregations = user_input.aggregations.split(',')
            show_aggregations = True
        if "tutored" in user_input:
            if user_input.tutored == "aggregations":
                checked_aggregations = tutored_aggregations
                show_aggregations = True
            elif user_input.tutored == "users":
                checked_users = tutored_users
                show_aggregations = True
        if "format" in user_input and user_input.format in self.valid_formats(course):
            chosen_format = user_input.format
            if "aggregation" in chosen_format:
                show_aggregations = True

        for aggregation in aggregations:
            aggregation['checked'] = str(aggregation['_id']) in checked_aggregations

        return self.template_helper.get_renderer().course_admin.download(course,
                                                                         tasks, user_data, aggregations,
                                                                         tutored_aggregations, tutored_users,
                                                                         checked_tasks, checked_users,
                                                                         self.valid_formats(course), chosen_format,
                                                                         show_aggregations)
