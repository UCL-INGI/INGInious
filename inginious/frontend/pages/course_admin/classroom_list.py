# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web
from bson.objectid import ObjectId

import inginious.common.custom_yaml as yaml
from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseClassroomListPage(INGIniousAdminPage):
    """ Course administration page: list of classrooms """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="classrooms.yaml"', unique=True)
            classrooms = [{"description": classroom["description"],
                           "students": classroom["students"],
                           "tutors": classroom["tutors"]} for classroom in
                          self.user_manager.get_course_classrooms(course)]

            return yaml.dump(classrooms)

        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)

        error = False
        try:
            if self.user_manager.has_admin_rights_on_course(course):
                data = web.input()
                if 'classroom' in data:
                    self.database.classrooms.insert({"courseid": courseid, "students": [],
                                                     "tutors": [],
                                                     "description": data['classroom']})
                    msg = _("New classroom created.")
                else:  # default, but with no classroom detected
                    msg = _("Invalid classroom selected.")
            else:
                msg = _("You have no rights to add/change classrooms")
                error = True
        except:
            msg = _('User returned an invalid form.')
            error = True

        return self.page(course, msg, error)

    def submission_url_generator(self, classroomid):
        """ Generates a submission url """
        return "?format=taskid%2Fclassroom&classrooms=" + str(classroomid)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        classrooms = OrderedDict()
        taskids = list(course.get_tasks().keys())

        for classroom in self.user_manager.get_course_classrooms(course):
            classrooms[classroom['_id']] = dict(list(classroom.items()) +
                                                [("tried", 0),
                                                 ("done", 0),
                                                 ("url", self.submission_url_generator(classroom['_id']))
                                                 ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": taskids},
                                "username": {"$in": classroom["students"]}
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
                classrooms[classroom['_id']]["tried"] += 1 if c["tried"] else 0
                classrooms[classroom['_id']]["done"] += 1 if c["done"] else 0

        my_classrooms, other_classrooms = [], []
        for classroom in classrooms.values():
            if self.user_manager.session_username() in classroom["tutors"]:
                my_classrooms.append(classroom)
            else:
                other_classrooms.append(classroom)

        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.classroom_list(course, [my_classrooms, other_classrooms], msg, error)
