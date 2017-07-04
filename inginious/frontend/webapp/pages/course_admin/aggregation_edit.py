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


class CourseEditAggregation(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course, aggregationid=''):
        """ Get the available student and tutor lists for aggregation edition"""
        tutor_list = course.get_staff()

        # Determine student list and if they are grouped
        student_list = list(self.database.aggregations.aggregate([
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
        users_info = self.user_manager.get_users_info(list(student_list.keys()) + tutor_list)

        if aggregationid:
            # Order the non-registered students
            other_students = [student_list[entry]['students'] for entry in student_list.keys() if
                              not student_list[entry]['classroom'] == ObjectId(aggregationid)]
            other_students = sorted(other_students, key=lambda val: (("0"+users_info[val][0]) if users_info[val] else ("1"+val)))

            return student_list, tutor_list, other_students, users_info
        else:
            return student_list, tutor_list, users_info

    def update_aggregation(self, course, aggregationid, new_data):
        """ Update aggregation and returns a list of errored students"""

        student_list = self.user_manager.get_course_registered_users(course, False)

        # If aggregation is new
        if aggregationid == 'None':
            # Remove _id for correct insertion
            del new_data['_id']
            new_data["courseid"] = course.get_id()

            # Insert the new aggregation
            result = self.database.aggregations.insert_one(new_data)

            # Retrieve new aggregation id
            aggregationid = result.inserted_id
            new_data['_id'] = result.inserted_id
            aggregation = new_data
        else:
            aggregation = self.database.aggregations.find_one({"_id": ObjectId(aggregationid), "courseid": course.get_id()})

        # Check tutors
        new_data["tutors"] = [tutor for tutor in new_data["tutors"] if tutor in course.get_staff()]

        students, groups, errored_students = [], [], []

        # Check the students
        for student in new_data["students"]:
            if student in student_list:
                # Remove user from the other aggregation
                self.database.aggregations.find_one_and_update({"courseid": course.get_id(), "groups.students": student},
                                                             {"$pull": {"groups.$.students": student, "students": student}})
                self.database.aggregations.find_one_and_update({"courseid": course.get_id(), "students": student}, {"$pull": {"students": student}})
                students.append(student)
            else:
                # Check if user can be registered
                user_info = self.user_manager.get_user_info(student)
                if user_info is None or student in aggregation["tutors"]:
                    errored_students.append(student)
                else:
                    students.append(student)

        removed_students = [student for student in aggregation["students"] if student not in new_data["students"]]
        self.database.aggregations.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                     {"$push": {"students": {"$each": removed_students}}})

        new_data["students"] = students

        # Check the groups
        for group in new_data["groups"]:
            group["students"] = [student for student in group["students"] if student in new_data["students"]]
            if len(group["students"]) <= group["size"]:
                groups.append(group)

        new_data["groups"] = groups

        # Check for default aggregation
        if new_data['default']:
            self.database.aggregations.find_one_and_update({"courseid": course.get_id(), "default": True},
                                                         {"$set": {"default": False}})

        aggregation = self.database.aggregations.find_one_and_update(
            {"_id": ObjectId(aggregationid)},
            {"$set": {"description": new_data["description"],
                      "students": students, "tutors": new_data["tutors"],
                      "groups": groups, "default": new_data['default']}}, return_document=ReturnDocument.AFTER)

        return aggregation, errored_students

    def display_page(self, course, aggregationid='', msg='', error=False):
        # If no aggregation id specified, use the groups only template
        if aggregationid:
            student_list, tutor_list, other_students, users_info = self.get_user_lists(course, aggregationid)
            aggregation = self.database.aggregations.find_one({"_id": ObjectId(aggregationid), "courseid": course.get_id()})

            if aggregation and course.use_classrooms():
                return self.template_helper.get_renderer().course_admin.classroom_edit(course, student_list, tutor_list,
                                                                                       other_students, users_info,
                                                                                       aggregation, msg, error)
            else:
                raise web.notfound()
        else:
            student_list, tutor_list, users_info = self.get_user_lists(course)
            aggregations = self.user_manager.get_course_aggregations(course)
            if course.use_classrooms():
                raise web.notfound()
            else:
                return self.template_helper.get_renderer().course_admin.teams_edit(course, student_list,
                                                                                        tutor_list,
                                                                                        users_info, aggregations, msg,
                                                                                        error)

    def GET_AUTH(self, courseid, aggregationid=''):  # pylint: disable=arguments-differ
        """ Edit a aggregation """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        if course.is_lti():
            raise web.notfound()

        return self.display_page(course, aggregationid)

    def POST_AUTH(self, courseid, aggregationid=''):  # pylint: disable=arguments-differ
        """ Edit a aggregation """
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        if course.is_lti():
            raise web.notfound()

        msg=''
        error = False
        errored_students = []
        data = web.input(delete=[], tutors=[], groups=[], aggregationfile={})
        if len(data["delete"]):

            for classid in data["delete"]:
                # Get the aggregation
                aggregation = self.database.aggregations.find_one({"_id": ObjectId(classid), "courseid": courseid}) if ObjectId.is_valid(classid) else None

                if aggregation is None:
                    msg = "Classroom" if course.use_classrooms() else "Team" + " with id " + classid + "not found."
                    error = True
                elif aggregation['default'] and aggregationid:
                    msg = "You can't remove your default classroom."
                    error = True
                else:
                    self.database.aggregations.find_one_and_update({"courseid": courseid, "default": True},
                                                                 {"$push": {
                                                                     "students": {"$each": aggregation["students"]}
                                                                 }})

                    self.database.aggregations.delete_one({"_id": ObjectId(classid)})
                    msg = "Classroom updated."

            if aggregationid and aggregationid in data["delete"]:
                raise web.seeother(self.app.get_homepath() + "/admin/" + courseid + "/aggregations")

        try:
            if "upload" in data:
                self.database.aggregations.delete_many({"courseid": course.get_id()})
                aggregations = custom_yaml.load(data["aggregationfile"].file)
            else:
                aggregations = json.loads(data["aggregations"])

            for index, new_aggregation in enumerate(aggregations):
                # In case of file upload, no id specified
                new_aggregation['_id'] = new_aggregation['_id'] if '_id' in new_aggregation else 'None'

                # In case of no aggregation usage, set the first entry default
                if not aggregationid and index == 0:
                    new_aggregation["default"] = True

                # If no groups field set, create group from class students if in groups only mode
                if "groups" not in new_aggregation:
                    new_aggregation["groups"] = [] if aggregationid else [{'size': len(new_aggregation['students']),
                                                                       'students': new_aggregation['students']}]

                # Update the aggregation
                aggregation, errors = self.update_aggregation(course, new_aggregation['_id'], new_aggregation)

                # If file upload was done, get the default aggregation id
                if course.use_classrooms() and aggregation['default']:
                    aggregationid = aggregation['_id']
                errored_students += errors

            if len(errored_students) > 0:
                msg = "Changes couldn't be applied for following students : <ul>"
                for student in errored_students:
                    msg += "<li>" + student + "</li>"
                msg += "</ul>"
                error = True
            elif not error:
                msg = "Classroom updated." if course.use_classrooms() else "Teams updated."
        except:
            msg = 'An error occurred while parsing the data.'
            error = True

        # Display the page
        return self.display_page(course, aggregationid, msg, error)
