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

from inginious.common import custom_yaml
import web
import json
from pymongo import ReturnDocument
from bson.objectid import ObjectId

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


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

        other_students = [entry['students'] for entry in list(self.database.classrooms.aggregate([
            {"$match": {"courseid": course.get_id(), "_id": {"$ne": ObjectId(classroomid)}}},
            {"$unwind": "$students"},
            {"$project": {"_id": 0, "students": 1}}
        ]))]

        users_info = self.user_manager.get_users_info(other_students + student_list.keys() + tutor_list)

        return student_list, tutor_list, other_students, users_info

    def update_classroom(self, course, classroomid, new_data):
        """ Update classroom and returns a list of errored students"""
        student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroomid)

        # Check tutors
        new_data["tutors"] = [tutor for tutor in new_data["tutors"] if tutor in tutor_list]

        students, groups, errored_students = [], [], []

        # Check the students
        for student in new_data["students"]:
            if student in student_list:
                students.append(student)
            else:
                if student in other_students:
                    # Remove user from the other classroom
                    self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "groups.students": student}, {"$pull": {"groups.$.students": student, "students": student}})
                    self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "students": student}, {"$pull": {"students": student}})
                    students.append(student)
                else:
                    # Check if user can be registered
                    user_info = self.user_manager.get_user_info(student)
                    if user_info is None or student in tutor_list:
                        errored_students.append(student)
                    else:
                        students.append(student)

        removed_students = [student for student in student_list if student not in new_data["students"]]
        self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                     {"$push": {"students": {"$each": removed_students}}})

        new_data["students"] = students

        # Check the groups
        for group in new_data["groups"]:
            group["students"] = [student for student in group["students"] if student in new_data["students"]]
            if len(group["students"]) <= group["size"]:
                groups.append(group)

        new_data["groups"] = groups

        classroom = self.database.classrooms.find_one_and_update(
            {"_id": ObjectId(classroomid)},
            {"$set": {"description": new_data["description"],
                      "students": students, "tutors": new_data["tutors"],
                      "groups": groups}}, return_document=ReturnDocument.AFTER)

        return classroom, errored_students

    def GET(self, courseid, classroomid):
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroomid)
        classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})

        if classroom:
            return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, other_students, users_info, classroom, "", False)
        else:
            raise web.notfound()

    def POST(self, courseid, classroomid):
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        error = False
        try:
            data = web.input(tutors=[], groups=[], classroomfile={})
            if "delete" in data:
                # Get the classroom
                classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})

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
            else:
                if "upload" in data:
                    new_data = custom_yaml.load(data["classroomfile"].file)
                else:
                    # Prepare classroom-like data structure from input
                    new_data = {"description": data["description"], "tutors": data["tutors"], "students": [], "groups": []}
                    for index, groupstr in enumerate(data["groups"]):
                        group = json.loads(groupstr)
                        new_data["students"].extend(group["students"])
                        if index != 0:
                            new_data["groups"].append(group)

                classroom, errored_students = self.update_classroom(course, classroomid, new_data)
                student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroom["_id"])

                if len(errored_students) > 0:
                    msg = "Changes couldn't be applied for following students : <ul>"
                    for student in errored_students:
                        msg += "<li>" + student + "</li>"
                    msg += "</ul>"
                    error = True
                else :
                    msg = "Classroom updated."

        except:
            classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})
            student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroom["_id"])
            msg = 'An error occurred while parsing the data.'
            error = True

        return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, other_students, users_info, classroom, msg, error)
