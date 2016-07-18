# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

from bson.objectid import ObjectId
import inginious.common.custom_yaml as yaml
import web

from inginious.frontend.webapp.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseClassroomListPage(INGIniousAdminPage):
    """ Course administration page: list of classrooms """

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="classrooms.yaml"', unique=True)
            if course.use_classrooms():
                classrooms = [{"default": classroom["default"],
                               "description": classroom["description"],
                               "groups": classroom["groups"],
                               "students": classroom["students"],
                               "tutors": classroom["tutors"]} for classroom in
                              self.user_manager.get_course_classrooms(course)]
            else:
                classrooms = [{"default": classroom["default"],
                               "description": classroom["description"],
                               "groups": classroom["groups"],
                               "students": classroom["students"],
                               "tutors": classroom["tutors"]} for classroom in
                              self.user_manager.get_course_classrooms(course) if len(classroom["groups"])>0]

            return yaml.dump(classrooms)

        return self.page(course)

    def POST(self, courseid):
        """ POST request """
        course, _ = self.get_course_and_check_rights(courseid)

        error = False
        try:
            if self.user_manager.has_admin_rights_on_course(course):
                data = web.input()
                if 'classroom' in data:
                    default = True if self.database.classrooms.find_one({"courseid": courseid, "default": True}) is None else False
                    self.database.classrooms.insert({"default": default, "courseid": courseid, "students": [],
                                                     "tutors": [], "groups": [],
                                                     "description": data['classroom']})
                    msg = "New classroom created."
                elif 'default' in data:
                    self.database.classrooms.find_one_and_update({"courseid": courseid, "default": True},
                                                                 {"$set": {"default": False}})
                    self.database.classrooms.find_one_and_update({"_id": ObjectId(data['default'])},
                                                                 {"$set": {"default": True}})
                    msg = "Default classroom changed."
            else:
                msg = "You have no rights to add/change classrooms"
                error = True
        except:
            msg = 'User returned an invalid form.'
            error = True

        return self.page(course, msg, error)

    def submission_url_generator(self, course, classroomid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "/download?format=taskid%2Fclassroom&classrooms=" + str(classroomid)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        classrooms = OrderedDict()

        for classroom in self.user_manager.get_course_classrooms(course):
            classrooms[classroom['_id']] = dict(classroom.items() +
                                                [("tried", 0),
                                                 ("done", 0),
                                                 ("url", self.submission_url_generator(course, classroom['_id']))
                                                 ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": course.get_tasks().keys()},
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
