# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web
import yaml

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentListPage(INGIniousAdminPage):
    """ Course administration page: list of registered students """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        if "download_audiences" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="audiences.yaml"', unique=True)
            audiences = [{"description": audience["description"],
                           "students": audience["students"],
                           "tutors": audience["tutors"]} for audience in
                          self.user_manager.get_course_audiences(course)]

            return yaml.dump(audiences)

        return self.page(course, active_tab="tab_audiences" if "audiences" in web.input() else "tab_students")

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid, None, False)
        data = web.input()
        error = {}
        msg = {}
        active_tab = "tab_students"

        self.post_student_list(course, data)
        active_tab = self.post_audiences(course, msg, error, active_tab)

        return self.page(course, active_tab, msg, error)

    def submission_url_generator_user(self, username):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&users=" + username

    def submission_url_generator_audience(self, audienceid):
        """ Generates a submission url """
        return "?audiences=" + str(audienceid)

    def page(self, course, active_tab="tab_students", msg=None, error=None):
        """ Get all data and display the page """
        if error is None:
            error = {}
        if msg is None:
            msg = {}

        split_audiences, audiences = self.get_audiences_params(course)
        user_data = self.get_student_list_params(course)

        if "csv_audiences" in web.input():
            return make_csv(audiences)
        if "csv_student" in web.input():
            return make_csv(user_data)

        return self.template_helper.get_renderer().course_admin.student_list(course, list(user_data.values()),
                                                                             split_audiences, active_tab, error, msg)

    def get_student_list_params(self, course):
        users = sorted(list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items()),
                       key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(list(self.user_manager.get_users_info(course.get_staff()).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else "") + users)

        user_data = OrderedDict([(username, {
            "username": username, "realname": user[0] if user is not None else "",
            "email": user[1] if user is not None else "", "total_tasks": 0,
            "task_grades": {"answer": 0, "match": 0}, "task_succeeded": 0, "task_tried": 0, "total_tries": 0,
            "grade": 0, "url": self.submission_url_generator_user(username)}) for username, user in users.items()])

        for username, data in self.user_manager.get_course_caches(list(users.keys()), course).items():
            user_data[username].update(data if data is not None else {})

        return user_data

    def get_audiences_params(self, course):
        audiences = OrderedDict()
        taskids = list(course.get_tasks().keys())

        for audience in self.user_manager.get_course_audiences(course):
            audiences[audience['_id']] = dict(list(audience.items()) +
                                              [("tried", 0),
                                               ("done", 0),
                                               ("url", self.submission_url_generator_audience(audience['_id']))
                                               ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": taskids},
                                "username": {"$in": audience["students"]}
                            }
                    },
                    {
                        "$group":
                            {
                                "_id": "$taskid",
                                "tried": {"$sum": 1},
                                "done": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}}
                            }
                    },

                ]))

            for c in data:
                audiences[audience['_id']]["tried"] += 1 if c["tried"] else 0
                audiences[audience['_id']]["done"] += 1 if c["done"] else 0

        my_audiences, other_audiences = [], []
        for audience in audiences.values():
            if self.user_manager.session_username() in audience["tutors"]:
                my_audiences.append(audience)
            else:
                other_audiences.append(audience)

        return [my_audiences, other_audiences], audiences

    def post_student_list(self, course, data):
        if "remove_student" in data:
            try:
                if data["type"] == "all":
                    audiences = list(self.database.audiences.find({"courseid": course.get_id()}))
                    for audience in audiences:
                        audience["students"] = []
                        self.database.audiences.replace_one({"_id": audience["_id"]}, audience)
                    groups = list(self.database.groups.find({"courseid": course.get_id()}))
                    for group in groups:
                        group["students"] = []
                        self.database.groups.replace_one({"_id": group["_id"]}, group)
                    self.database.courses.find_one_and_update({"_id": course.get_id()}, {"$set": {"students": []}})
                else:
                    self.user_manager.course_unregister_user(course, data["username"])
            except:
                pass
        elif "register_student" in data:
            try:
                self.user_manager.course_register_user(course, data["username"].strip(), '', True)
            except:
                pass

    def post_audiences(self, course, msg, error, active_tab):
        try:
            data = web.input()
            if 'audience' in data:
                if self.user_manager.has_admin_rights_on_course(course):

                    self.database.audiences.insert({"courseid": course.get_id(), "students": [],
                                                     "tutors": [],
                                                     "description": data['audience']})
                    msg["audiences"] = _("New audience created.")
                else:
                    msg["audiences"] = _("You have no rights to add/change audiences")
                    error["audiences"] = True
                active_tab = "tab_audiences"

        except:
            msg["audiences"] = _('User returned an invalid form.')
            error["audiences"] = True
            active_tab = "tab_audiences"
        return active_tab
