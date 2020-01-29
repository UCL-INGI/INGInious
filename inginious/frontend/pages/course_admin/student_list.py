# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseStudentListPage(INGIniousAdminPage):
    """ Course administration page: list of registered students """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid, None, False)
        data = web.input()
        if "remove" in data:
            try:
                if data["type"] == "all":
                    audiences = list(self.database.audiences.find({"courseid": courseid}))
                    for audience in audiences:
                        audience["students"] = []
                        self.database.audiences.replace_one({"_id": audience["_id"]}, audience)
                    groups = list(self.database.groups.find({"courseid": courseid}))
                    for group in groups:
                        group["students"] = []
                        self.database.groups.replace_one({"_id": group["_id"]}, group)
                    self.database.courses.find_one_and_update({"_id": course.get_id()}, {"$set": {"students": []}})
                else:
                    self.user_manager.course_unregister_user(course, data["username"])
            except:
                pass
        elif "register" in data:
            try:
                self.user_manager.course_register_user(course, data["username"].strip(), '', True)
            except:
                pass
        return self.page(course)

    def submission_url_generator(self, username):
        """ Generates a submission url """
        return "?format=taskid%2Fusername&users=" + username

    def page(self, course, error="", post=False):
        """ Get all data and display the page """
        users = sorted(list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course, False)).items()),
                       key=lambda k: k[1][0] if k[1] is not None else "")

        users = OrderedDict(sorted(list(self.user_manager.get_users_info(course.get_staff()).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else "") + users)

        user_data = OrderedDict([(username, {
            "username": username, "realname": user[0] if user is not None else "",
            "email": user[1] if user is not None else "", "total_tasks": 0,
            "task_grades": {"answer": 0, "match": 0}, "task_succeeded": 0, "task_tried": 0, "total_tries": 0,
            "grade": 0, "url": self.submission_url_generator(username)}) for username, user in users.items()])

        for username, data in self.user_manager.get_course_caches(list(users.keys()), course).items():
            user_data[username].update(data if data is not None else {})

        if "csv" in web.input():
            return make_csv(user_data)

        return self.template_helper.get_renderer().course_admin.student_list(course, list(user_data.values()), error, post)
