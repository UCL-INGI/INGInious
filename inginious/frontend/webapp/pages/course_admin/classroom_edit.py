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

    def get_user_lists(self, course, classroomid=''):
        """ Get the available student and tutor lists for classroom edition"""
        tutor_list = course.get_staff()

        # Determine student list and if they are grouped
        student_list = list(self.database.classrooms.aggregate([
            {"$match": {"courseid": course.get_id()}},
            {"$unwind": "$students"},
            {"$project": {
                "classroom": "$_id",
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
        users_info = self.user_manager.get_users_info(student_list.keys() + tutor_list)

        if classroomid:
            # Order the non-registered students
            other_students = [student_list[entry]['students'] for entry in student_list.keys() if
                              not student_list[entry]['classroom'] == ObjectId(classroomid)]
            other_students = sorted(other_students, key=lambda val: (("0"+users_info[val][0]) if users_info[val] else ("1"+val)))

            return student_list, tutor_list, other_students, users_info
        else:
            return student_list, tutor_list, users_info

    def update_classroom(self, course, classroomid, new_data):
        """ Update classroom and returns a list of errored students"""

        student_list = self.user_manager.get_course_registered_users(course, False)

        # If classroom is new
        if classroomid == 'None':
            # Remove _id for correct insertion
            del new_data['_id']
            new_data["courseid"] = course.get_id()

            # Insert the new classroom
            result = self.database.classrooms.insert_one(new_data)

            # Retrieve new classroom id
            classroomid = result.inserted_id
            new_data['_id'] = result.inserted_id
            classroom = new_data
        else:
            classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": course.get_id()})

        # Check tutors
        new_data["tutors"] = [tutor for tutor in new_data["tutors"] if tutor in course.get_tutors()]

        students, groups, errored_students = [], [], []

        # Check the students
        for student in new_data["students"]:
            if student in student_list:
                # Remove user from the other classroom
                self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "groups.students": student},
                                                             {"$pull": {"groups.$.students": student, "students": student}})
                self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "students": student}, {"$pull": {"students": student}})
                students.append(student)
            else:
                # Check if user can be registered
                user_info = self.user_manager.get_user_info(student)
                if user_info is None or student in classroom["tutors"]:
                    errored_students.append(student)
                else:
                    students.append(student)

        removed_students = [student for student in classroom["students"] if student not in new_data["students"]]
        self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                     {"$push": {"students": {"$each": removed_students}}})

        new_data["students"] = students

        # Check the groups
        for group in new_data["groups"]:
            group["students"] = [student for student in group["students"] if student in new_data["students"]]
            if len(group["students"]) <= group["size"]:
                groups.append(group)

        new_data["groups"] = groups

        # Check for default classroom
        if new_data['default']:
            self.database.classrooms.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                         {"$set": {"default": False}})

        classroom = self.database.classrooms.find_one_and_update(
            {"_id": ObjectId(classroomid)},
            {"$set": {"description": new_data["description"],
                      "students": students, "tutors": new_data["tutors"],
                      "groups": groups, "default": new_data['default']}}, return_document=ReturnDocument.AFTER)

        return classroom, errored_students

    def display_page(self, course, classroomid='', msg='', error=False):
        # If no classroom id specified, use the groups only template
        if classroomid:
            student_list, tutor_list, other_students, users_info = self.get_user_lists(course, classroomid)
            classroom = self.database.classrooms.find_one({"_id": ObjectId(classroomid), "courseid": course.get_id()})

            if classroom and course.use_classrooms():
                return self.template_helper.get_renderer().course_admin.edit_classroom(course, student_list, tutor_list,
                                                                                       other_students, users_info,
                                                                                       classroom, msg, error)
            else:
                raise web.notfound()
        else:
            student_list, tutor_list, users_info = self.get_user_lists(course)
            classrooms = list(self.database.classrooms.find({"courseid": course.get_id()}))
            if course.use_classrooms():
                raise web.notfound()
            else:
                return self.template_helper.get_renderer().course_admin.edit_classrooms(course, student_list,
                                                                                        tutor_list,
                                                                                        users_info, classrooms, msg,
                                                                                        error)

    def GET(self, courseid, classroomid=''):
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=True)
        return self.display_page(course, classroomid)

    def POST(self, courseid, classroomid=''):
        """ Edit a classroom """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        msg=''
        error = False
        errored_students = []
        data = web.input(delete=[], tutors=[], groups=[], classroomfile={})
        if len(data["delete"]):

            for classid in data["delete"]:
                # Get the classroom
                classroom = self.database.classrooms.find_one({"_id": ObjectId(classid), "courseid": courseid})

                if classroom is None:
                    msg = "Classroom not found."
                    error = True
                elif classroom['default'] and classroomid:
                    msg = "You can't remove your default classroom."
                    error = True
                else:
                    self.database.classrooms.find_one_and_update({"courseid": courseid, "default": True},
                                                                 {"$push": {
                                                                     "students": {"$each": classroom["students"]}
                                                                 }})

                    self.database.classrooms.delete_one({"_id": ObjectId(classid)})
                    msg = "Classroom updated."

            if classroomid and classroomid in data["delete"]:
                raise web.seeother("/admin/" + courseid + "/classrooms")

        try:
            if "upload" in data:
                self.database.classrooms.delete_many({"courseid": course.get_id()})
                classrooms = custom_yaml.load(data["classroomfile"].file)
            else:
                classrooms = json.loads(data["classrooms"])

            for index, new_classroom in enumerate(classrooms):
                # In case of file upload, no id specified
                new_classroom['_id'] = new_classroom['_id'] if '_id' in new_classroom else 'None'

                # In case of no classroom usage, set the first entry default
                if not classroomid and index == 0:
                    new_classroom["default"] = True

                # If no groups field set, create group from class students if in groups only mode
                if "groups" not in new_classroom:
                    new_classroom["groups"] = [] if classroomid else [{'size': len(new_classroom['students']),
                                                                       'students': new_classroom['students']}]

                # Update the classroom
                classroom, errors = self.update_classroom(course, new_classroom['_id'], new_classroom)

                # If file upload was done, get the default classroom id
                if course.use_classrooms() and classroom['default']:
                    classroomid = classroom['_id']
                errored_students += errors

            if len(errored_students) > 0:
                msg = "Changes couldn't be applied for following students : <ul>"
                for student in errored_students:
                    msg += "<li>" + student + "</li>"
                msg += "</ul>"
                error = True
            else:
                msg = "Classroom updated."
        except:
            msg = 'An error occurred while parsing the data.'
            error = True

        # Display the page
        return self.display_page(course, classroomid, msg, error)
