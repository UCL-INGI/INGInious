# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """

import json

import flask
from flask import redirect
from werkzeug.exceptions import NotFound
from bson.objectid import ObjectId

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseEditAudience(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course, audienceid=''):
        """ Get the available student and tutor lists for audience edition"""
        tutor_list = course.get_admins()
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
            other_students = sorted(other_students, key=lambda val: (("0"+users_info[val].realname) if users_info[val] else ("1"+val)))

            return student_list, tutor_list, other_students, users_info
        else:
            return student_list, tutor_list, users_info

    def display_page(self, course, audienceid, msg='', error=False):
        audience = self.database.audiences.find_one({"_id": ObjectId(audienceid), "courseid": course.get_id()})
        if not audience:
            raise NotFound(description=_("This audience doesn't exist."))

        student_list, tutor_list, other_students, users_info = self.get_user_lists(course, audienceid)
        return self.template_helper.render("course_admin/audience_edit.html", course=course, student_list=student_list,
                                           tutor_list=tutor_list,other_students=other_students, users_info=users_info,
                                           audience=audience, msg=msg, error=error)

    def GET_AUTH(self, courseid, audienceid):  # pylint: disable=arguments-differ
        """ Edit a audience """
        course, __ = self.get_course_and_check_rights(courseid)

        return self.display_page(course, audienceid)

    def POST_AUTH(self, courseid, audienceid=''):  # pylint: disable=arguments-differ
        """ Edit a audience """
        course, __ = self.get_course_and_check_rights(courseid)
        msg=''
        error = False

        data = flask.request.form.copy()
        data["delete"] = flask.request.form.getlist("delete")
        data["tutors"] = flask.request.form.getlist("tutors")

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
                return redirect(self.app.get_homepath() + "/admin/" + courseid + "/students?audiences")
        else:
            audiences_dict = json.loads(data["audiences"])
            student_list = self.user_manager.get_course_registered_users(course, False)
            for username in audiences_dict[0]["students"]:
                userdata = self.database.users.find_one({"username": username})
                if userdata is None:
                    msg = _("User not found : {}".format(username))
                    error = True
                    # Display the page
                    return self.display_page(course, audienceid, msg, error)
                elif username not in student_list:
                    self.user_manager.course_register_user(course, username, force=True)
            self.database.audiences.update_one(
                {"_id": ObjectId(audiences_dict[0]["_id"])},
                {"$set": {"students": audiences_dict[0]["students"],
                          "tutors": audiences_dict[0]["tutors"],
                          "description": str(audiences_dict[0]["description"])}}) \
                if ObjectId.is_valid(audiences_dict[0]["_id"]) else None
            msg = _("Audience updated.")

        # Display the page
        return self.display_page(course, audienceid, msg, error)
