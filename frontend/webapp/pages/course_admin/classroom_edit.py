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
""" Pages that allow editing of tasks """

import web
import json
from pymongo import ReturnDocument
from bson.objectid import ObjectId

from frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseEditClassroom(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course, classroomid):
        """ Get the available student and tutor lists for classroom edition"""
        tutor_list = course.get_staff()

        # Determine if user is grouped or not in the classroom
        student_list = list(self.database.classrooms.aggregate([
            {"$match": {"_id": ObjectId(classroomid)}},
            {"$unwind": "$students"},
            {"$project": {
                "students": 1,
                "grouped": {
                    "$anyElementTrue": {
                        "$map": {
                            "input": "$groups.students",
                            "as": "group",
                            "in": {
                                "$anyElementTrue": {
                                    "$map":{
                                        "input": "$$group",
                                        "as": "groupmember",
                                        "in": {"$eq": ["$$groupmember", "$students"]}
                                    }
                                }
                            }
                        }
                    }
                }
            }}
        ]))

        student_list = dict([(student["students"], student) for student in student_list])

        return student_list, tutor_list

    def GET(self, courseid, classroomid):
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        student_list, tutor_list = self.get_user_lists(course, classroomid)

        classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})

        if classroom:
            return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, classroom, "", False)
        else:
            raise web.notfound()

    def POST(self, courseid, classroomid):
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        student_list, tutor_list = self.get_user_lists(course, classroomid)
        classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})

        error = False
        try:
            data = web.input(tutors=[], groups=[])
            if "delete" in data:
                if classroom['default']:
                    msg = "You can't remove your default classroom."
                    error = True
                else:
                    self.database.classrooms.find_one_and_update({"courseid": courseid, "default": True},
                                                                 {"$push": {
                                                                     "students": {"$each": classroom["students"]}
                                                                 }})

                    self.database.classrooms.delete_one({"_id": ObjectId(classroomid)})
                    raise web.seeother("/admin/" + courseid + "/classrooms")
            elif "upload" in data:
                msg = "New classroom settings uploaded."
            else:
                # Check tutors
                data["tutors"] = [tutor for tutor in data["tutors"] if tutor in tutor_list]

                students, groups, errored_students = [], [], []
                # Generate groups structure
                for groupstr in data["groups"]:
                    group = json.loads(groupstr)

                    # Check students
                    for student in group["students"]:
                        if student not in student_list:
                            errored_students.append(student)
                        else:
                            student_list[student]["grouped"] = True if (group["size"] > 0 and group["size"] >= len(group["students"])) else False
                            students.append(student)

                    # Remove errored students from group
                    group["students"] = [student for student in group["students"] if student not in errored_students]
                    if group["size"] > 0 and group["size"] >= len(group["students"]):
                        groups.append(group)

                if len(errored_students) > 0:
                    msg = "Changes couldn't be applied for following students : <ul>"
                    for student in errored_students:
                        msg += "<li>" + student + "</li>"
                    msg += "</ul>"
                    error = True
                else :
                    msg = "Classroom updated."

                classroom = self.database.classrooms.find_one_and_update(
                    {"_id": ObjectId(classroomid)},
                    {"$set": {"description": data["description"],
                              "students": students, "tutors": data["tutors"],
                              "groups": groups}}, return_document=ReturnDocument.AFTER)

        except:
            msg = 'An error occurred while parsing the form data.'
            error = True

        return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, classroom, msg, error)
