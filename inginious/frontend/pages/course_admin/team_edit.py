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


class CourseEditTeam(INGIniousAdminPage):
    """ Edit a task """

    def get_user_lists(self, course):
        """ Get the available student and tutor lists for team edition"""
        tutor_list = course.get_staff()
        audience_list = self.user_manager.get_course_audiences(course)
        audience_list = {audience["_id"]: audience for audience in audience_list}

        student_list = self.user_manager.get_course_registered_users(course, False)
        users_info = self.user_manager.get_users_info(student_list + tutor_list)

        teams_list = list(self.database.teams.aggregate([
            {"$match": {"courseid": course.get_id()}},
            {"$unwind": "$students"},
            {"$project": {
                "team": "$_id",
                "students": 1
            }}
        ]))
        teams_list = {d["students"]: d["team"] for d in teams_list}

        other_students = [entry for entry in student_list if entry not in teams_list]
        other_students = sorted(other_students, key=lambda val: (("0"+users_info[val][0]) if users_info[val] else ("1"+val)))

        return student_list, tutor_list, audience_list, other_students, users_info

    def update_team(self, course, teamid, new_data, audience_students):
        """ Update team and returns a list of errored students"""

        student_list = self.user_manager.get_course_registered_users(course, False)

        # If team is new
        if teamid == 'None':
            # Remove _id for correct insertion
            del new_data['_id']
            new_data["courseid"] = course.get_id()

            # Insert the new team
            result = self.database.teams.insert_one(new_data)

            # Retrieve new team id
            teamid = result.inserted_id
            new_data['_id'] = result.inserted_id
            team = new_data
        else:
            team = self.database.teams.find_one({"_id": ObjectId(teamid), "courseid": course.get_id()})

        # Convert audience ids to ObjectId
        new_data["audiences"] = [ObjectId(s) for s in new_data["audiences"]]

        # Check tutors
        new_data["tutors"] = [tutor for tutor in new_data["tutors"] if tutor in course.get_staff()]

        students, errored_students = [], []

        if len(new_data["students"]) <= new_data["size"]:
            # Check the students
            for student in new_data["students"]:
                student_allowed_in_team = any(set(audience_students.get(student, [])).intersection(new_data["audiences"]))
                if student in student_list and (student_allowed_in_team or not new_data["audiences"]):
                    # Remove user from the other team
                    self.database.teams.find_one_and_update({"courseid": course.get_id(), "students": student}, {"$pull": {"students": student}})
                    students.append(student)
                else:
                    errored_students.append(student)

        new_data["students"] = students

        team = self.database.teams.find_one_and_update(
            {"_id": ObjectId(teamid)},
            {"$set": {"description": new_data["description"], "audiences": new_data["audiences"], "size": new_data["size"],
                      "students": students, "tutors": new_data["tutors"]}}, return_document=ReturnDocument.AFTER)

        return team, errored_students

    def display_page(self, course, msg='', error=False):
        # If no team id specified, use the groups only template
        teams = self.user_manager.get_course_teams(course)
        student_list, tutor_list, audience_list, other_students, users_info = self.get_user_lists(course)
        return self.template_helper.get_renderer().course_admin.teams_edit(course, student_list, tutor_list,
                                                                           audience_list, other_students,
                                                                           users_info, teams, msg, error)

    def GET_AUTH(self, courseid, teamid=''):  # pylint: disable=arguments-differ
        """ Edit a team """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=True)

        if course.is_lti():
            raise web.notfound()

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="teams.yaml"', unique=True)
            teams = [{"description": team["description"],
                           "students": team["students"],
                           "size": team["size"],
                           "tutors": team["tutors"],
                            "audiences": [str(c) for c in team["audiences"]]} for team in
                          self.user_manager.get_course_teams(course)]

            return yaml.dump(teams)

        return self.display_page(course)

    def POST_AUTH(self, courseid, teamid=''):  # pylint: disable=arguments-differ
        """ Edit a team """
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
        data = web.input(delete=[], tutors=[], teamfile={})
        if len(data["delete"]):

            for classid in data["delete"]:
                # Get the team
                team = self.database.teams.find_one({"_id": ObjectId(classid), "courseid": courseid}) if ObjectId.is_valid(classid) else None

                if team is None:
                    msg = ("Team with id {} not found.").format(classid)
                    error = True
                else:
                    self.database.teams.find_one_and_update({"courseid": courseid},
                                                                 {"$push": {
                                                                     "students": {"$each": team["students"]}
                                                                 }})

                    self.database.teams.delete_one({"_id": ObjectId(classid)})
                    msg = _("Audience updated.")

            if teamid and teamid in data["delete"]:
                raise web.seeother(self.app.get_homepath() + "/admin/" + courseid + "/teams")

        try:
            if "upload" in data:
                self.database.teams.delete_many({"courseid": course.get_id()})
                teams = custom_yaml.load(data["teamfile"].file)
            else:
                teams = json.loads(data["teams"])

            for index, new_team in enumerate(teams):
                # In case of file upload, no id specified
                new_team['_id'] = new_team['_id'] if '_id' in new_team else 'None'

                # Update the team
                team, errors = self.update_team(course, new_team['_id'], new_team, audience_students)
                errored_students += errors

            if len(errored_students) > 0:
                msg = _("Changes couldn't be applied for following students :") + "<ul>"
                for student in errored_students:
                    msg += "<li>" + student + "</li>"
                msg += "</ul>"
                error = True
            elif not error:
                msg = _("Teams updated.")
        except:
            raise
            msg = _('An error occurred while parsing the data.')
            error = True

        # Display the page
        return self.display_page(course, msg, error)
