# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """

import json

import web
from bson.objectid import ObjectId
from pymongo import ReturnDocument

from inginious.common import custom_yaml
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseEditAudience(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course, audienceid=''):
        """ Get the available student and tutor lists for audience edition"""
        tutor_list = course.get_staff()
        student_list = self.user_manager.get_course_registered_users(course, False)
        users_info = self.user_manager.get_users_info(student_list + tutor_list)

        audiences_list = list(self.database.audiences.aggregate([
            {"$match": {"courseid": course.get_id()}},
            {"$unwind": "$students"},
            {"$project": {
                "audience": "$_id",
                "students": 1
            }}
        ]))
        audiences_list = {d["students"]: d["audience"] for d in audiences_list}

        if audienceid:
            # Order the non-registered students
            other_students = [entry for entry in student_list if not audiences_list.get(entry, {}) == ObjectId(audienceid)]
            other_students = sorted(other_students, key=lambda val: (("0"+users_info[val][0]) if users_info[val] else ("1"+val)))

            return student_list, tutor_list, other_students, users_info
        else:
            return student_list, tutor_list, users_info

    def update_audience(self, course, audienceid, new_data):
        """ Update audience and returns a list of errored students"""

        student_list = self.user_manager.get_course_registered_users(course, False)

        # If audience is new
        if audienceid == 'None':
            # Remove _id for correct insertion
            del new_data['_id']
            new_data["courseid"] = course.get_id()

            # Insert the new audience
            result = self.database.audiences.insert_one(new_data)

            # Retrieve new audience id
            audienceid = result.inserted_id
            new_data['_id'] = result.inserted_id
            audience = new_data
        else:
            audience = self.database.audiences.find_one({"_id": ObjectId(audienceid), "courseid": course.get_id()})

        # Check tutors
        new_data["tutors"] = [tutor for tutor in new_data["tutors"] if tutor in course.get_staff()]

        students, errored_students = [], []

        # Check the students
        for student in new_data["students"]:
            if student in student_list:
                students.append(student)
            else:
                # Check if user can be registered
                user_info = self.user_manager.get_user_info(student)
                if user_info is None or student in audience["tutors"]:
                    errored_students.append(student)
                else:
                    self.user_manager.course_register_user(course, student, force=True)
                    students.append(student)

        removed_students = [student for student in audience["students"] if student not in new_data["students"]]
        self.database.audiences.find_one_and_update({"courseid": course.get_id()},
                                                     {"$push": {"students": {"$each": removed_students}}})

        new_data["students"] = students

        audience = self.database.audiences.find_one_and_update(
            {"_id": ObjectId(audienceid)},
            {"$set": {"description": new_data["description"],
                      "students": students, "tutors": new_data["tutors"]}}, return_document=ReturnDocument.AFTER)

        return audience, errored_students

    def display_page(self, course, audienceid, msg='', error=False):
        audience = self.database.audiences.find_one({"_id": ObjectId(audienceid), "courseid": course.get_id()})
        if not audience:
            raise web.notfound()

        student_list, tutor_list, other_students, users_info = self.get_user_lists(course, audienceid)
        return self.template_helper.get_renderer().course_admin.audience_edit(course, student_list, tutor_list,
                                                                                   other_students, users_info,
                                                                                   audience, msg, error)

    def GET_AUTH(self, courseid, audienceid):  # pylint: disable=arguments-differ
        """ Edit a audience """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        return self.display_page(course, audienceid)

    def POST_AUTH(self, courseid, audienceid=''):  # pylint: disable=arguments-differ
        """ Edit a audience """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        msg=''
        error = False
        errored_students = []
        data = web.input(delete=[], tutors=[], audiencefile={})
        if len(data["delete"]):

            for classid in data["delete"]:
                # Get the audience
                audience = self.database.audiences.find_one({"_id": ObjectId(classid), "courseid": courseid}) if ObjectId.is_valid(classid) else None

                if audience is None:
                    msg = _("Audience with id {} not found.").format(classid)
                    error = True
                else:
                    self.database.audiences.find_one_and_update({"courseid": courseid},
                                                                 {"$push": {
                                                                     "students": {"$each": audience["students"]}
                                                                 }})

                    self.database.audiences.delete_one({"_id": ObjectId(classid)})
                    msg = _("Audience updated.")

            if audienceid and audienceid in data["delete"]:
                raise web.seeother(self.app.get_homepath() + "/admin/" + courseid + "/audiences")

        try:
            if "upload" in data:
                self.database.audiences.delete_many({"courseid": course.get_id()})
                audiences = custom_yaml.load(data["audiencefile"].file)
            else:
                audiences = json.loads(data["audiences"])

            for index, new_audience in enumerate(audiences):
                # In case of file upload, no id specified
                new_audience['_id'] = new_audience['_id'] if '_id' in new_audience else 'None'

                # Update the audience
                audience, errors = self.update_audience(course, new_audience['_id'], new_audience)

                # If file upload was done, get the default audience id
                audienceid = audience['_id']
                errored_students += errors

            if len(errored_students) > 0:
                msg = _("Changes couldn't be applied for following students :") + "<ul>"
                for student in errored_students:
                    msg += "<li>" + student + "</li>"
                msg += "</ul>"
                error = True
            elif not error:
                msg = _("Audience updated.")
        except:
            msg = _('An error occurred while parsing the data.')
            error = True

        # Display the page
        return self.display_page(course, audienceid, msg, error)
