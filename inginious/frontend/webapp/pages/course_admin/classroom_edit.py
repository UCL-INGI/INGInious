# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """

import json

import web
from pymongo import ReturnDocument
from bson.objectid import ObjectId

from inginious.common import custom_yaml
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
                                    "$map": {
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

        users_info = self.user_manager.get_users_info(other_students + list(student_list.keys()) + tutor_list)

        # Order the non-registered students
        other_students = sorted(other_students, key=lambda val: (("0"+users_info[val][0]) if users_info[val] else ("1"+val)))

        return student_list, tutor_list, other_students, users_info

    def update_classroom(self, course, classroomid, new_data):
        """ Update classroom and returns a list of errored students"""
        student_list, tutor_list, other_students, _ = self.get_user_lists(course, classroomid)

        # Check tutors
        new_data["tutors"] = [tutor for tutor in map(str.strip, new_data["tutors"]) if tutor in tutor_list]

        students, groups, errored_students = [], [], []

        new_data["students"] = map(str.strip, new_data["students"])

        # Check the students
        for student in new_data["students"]:
            if student in student_list:
                students.append(student)
            else:
                if student in other_students:
                    # Remove user from the other classroom
                    self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "groups.students": student},
                                                                 {"$pull": {"groups.$.students": student, "students": student}})
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
            group["students"] = [student for student in map(str.strip, group["students"]) if student in new_data["students"]]
            if len(group["students"]) <= group["size"]:
                groups.append(group)

        new_data["groups"] = groups

        classroom = self.database.classrooms.find_one_and_update(
            {"_id": ObjectId(classroomid)},
            {"$set": {"description": new_data["description"],
                      "students": students, "tutors": new_data["tutors"],
                      "groups": groups}}, return_document=ReturnDocument.AFTER)

        return classroom, errored_students

    def GET_AUTH(self, courseid, classroomid):  # pylint: disable=arguments-differ
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=True)
        if course.is_lti():
            raise web.notfound()

        student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroomid)
        classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})

        if classroom:
            return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, other_students, users_info,
                                                                                   classroom, "", False)
        else:
            raise web.notfound()

    def POST_AUTH(self, courseid, classroomid):  # pylint: disable=arguments-differ
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        if course.is_lti():
            raise web.notfound()

        error = False
        data = web.input(tutors=[], groups=[], classroomfile={})
        if "delete" in data:
            # Get the classroom
            classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})

            if classroom is None:
                msg = "Classroom not found."
                error = True
            elif classroom['default']:
                msg = "You can't remove your default classroom."
                error = True
            else:
                self.database.classrooms.find_one_and_update({"courseid": courseid, "default": True},
                                                             {"$push": {
                                                                 "students": {"$each": classroom["students"]}
                                                             }})

                self.database.classrooms.delete_one({"_id": ObjectId(classroomid)})
                raise web.seeother(self.app.get_homepath() + "/admin/" + courseid + "/classrooms")
        else:
            try:
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
                else:
                    msg = "Classroom updated."
            except:
                classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": courseid})
                student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroom["_id"])
                msg = 'An error occurred while parsing the data.'
                error = True

        return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list, other_students, users_info,
                                                                               classroom, msg, error)
