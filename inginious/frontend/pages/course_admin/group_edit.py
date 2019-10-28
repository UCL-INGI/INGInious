# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """

import json
import yaml

import web
from bson.objectid import ObjectId
from pymongo import ReturnDocument

from inginious.common import custom_yaml
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseEditGroup(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course):
        """ Get the available student list for group edition"""
        audience_list = self.user_manager.get_course_audiences(course)
        audience_list = {audience["_id"]: audience for audience in audience_list}

        student_list = self.user_manager.get_course_registered_users(course, False)
        users_info = self.user_manager.get_users_info(student_list)

        groups_list = list(self.database.groups.aggregate([
            {"$match": {"courseid": course.get_id()}},
            {"$unwind": "$students"},
            {"$project": {
                "group": "$_id",
                "students": 1
            }}
        ]))
        groups_list = {d["students"]: d["group"] for d in groups_list}

        other_students = [entry for entry in student_list if entry not in groups_list]
        other_students = sorted(other_students, key=lambda val: (("0"+users_info[val][0]) if users_info[val] else ("1"+val)))

        return student_list, audience_list, other_students, users_info

    def update_group(self, course, groupid, new_data, audience_students):
        """ Update group and returns a list of errored students"""

        student_list = self.user_manager.get_course_registered_users(course, False)

        # If group is new
        if groupid == 'None':
            # Remove _id for correct insertion
            del new_data['_id']
            new_data["courseid"] = course.get_id()

            # Insert the new group
            result = self.database.groups.insert_one(new_data)

            # Retrieve new group id
            groupid = result.inserted_id
            new_data['_id'] = result.inserted_id
            group = new_data
        else:
            group = self.database.groups.find_one({"_id": ObjectId(groupid), "courseid": course.get_id()})

        # Convert audience ids to ObjectId
        new_data["audiences"] = [ObjectId(s) for s in new_data["audiences"]]

        students, errored_students = [], []

        if len(new_data["students"]) <= new_data["size"]:
            # Check the students
            for student in new_data["students"]:
                student_allowed_in_group = any(set(audience_students.get(student, [])).intersection(new_data["audiences"]))
                if student in student_list and (student_allowed_in_group or not new_data["audiences"]):
                    # Remove user from the other group
                    self.database.groups.find_one_and_update({"courseid": course.get_id(), "students": student}, {"$pull": {"students": student}})
                    students.append(student)
                else:
                    errored_students.append(student)

        new_data["students"] = students

        group = self.database.groups.find_one_and_update(
            {"_id": ObjectId(groupid)},
            {"$set": {"description": new_data["description"], "audiences": new_data["audiences"], "size": new_data["size"],
                      "students": students}}, return_document=ReturnDocument.AFTER)

        return group, errored_students

    def display_page(self, course, msg='', error=False):
        # If no group id specified, use the groups only template
        groups = self.user_manager.get_course_groups(course)
        student_list, audience_list, other_students, users_info = self.get_user_lists(course)
        return self.template_helper.get_renderer().course_admin.groups_edit(course, student_list,
                                                                           audience_list, other_students,
                                                                           users_info, groups, msg, error)

    def GET_AUTH(self, courseid, groupid=''):  # pylint: disable=arguments-differ
        """ Edit a group """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        if course.is_lti():
            raise web.notfound()

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="groups.yaml"', unique=True)
            groups = [{"description": group["description"],
                           "students": group["students"],
                           "size": group["size"],
                            "audiences": [str(c) for c in group["audiences"]]} for group in
                          self.user_manager.get_course_groups(course)]

            return yaml.dump(groups)

        return self.display_page(course)

    def POST_AUTH(self, courseid, groupid=''):  # pylint: disable=arguments-differ
        """ Edit a group """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        if course.is_lti():
            raise web.notfound()

        audience_list = self.user_manager.get_course_audiences(course)
        audience_students = {}
        for audience in audience_list:
            for stud in audience["students"]:
                audience_students.setdefault(stud, []).append(audience["_id"])

        msg=''
        error = False
        errored_students = []
        data = web.input(delete=[], groupfile={})
        if len(data["delete"]):

            for classid in data["delete"]:
                # Get the group
                group = self.database.groups.find_one({"_id": ObjectId(classid), "courseid": courseid}) if ObjectId.is_valid(classid) else None

                if group is None:
                    msg = ("group with id {} not found.").format(classid)
                    error = True
                else:
                    self.database.groups.find_one_and_update({"courseid": courseid},
                                                                 {"$push": {
                                                                     "students": {"$each": group["students"]}
                                                                 }})

                    self.database.groups.delete_one({"_id": ObjectId(classid)})
                    msg = _("Audience updated.")

            if groupid and groupid in data["delete"]:
                raise web.seeother(self.app.get_homepath() + "/admin/" + courseid + "/groups")

        try:
            if "upload" in data:
                self.database.groups.delete_many({"courseid": course.get_id()})
                groups = custom_yaml.load(data["groupfile"].file)
            else:
                groups = json.loads(data["groups"])

            for index, new_group in enumerate(groups):
                # In case of file upload, no id specified
                new_group['_id'] = new_group['_id'] if '_id' in new_group else 'None'

                # Update the group
                group, errors = self.update_group(course, new_group['_id'], new_group, audience_students)
                errored_students += errors

            if len(errored_students) > 0:
                msg = _("Changes couldn't be applied for following students :") + "<ul>"
                for student in errored_students:
                    msg += "<li>" + student + "</li>"
                msg += "</ul>"
                error = True
            elif not error:
                msg = _("Groups updated.")
        except:
            raise
            msg = _('An error occurred while parsing the data.')
            error = True

        # Display the page
        return self.display_page(course, msg, error)
