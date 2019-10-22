# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """

import logging

import web
from bson.objectid import ObjectId

from inginious.frontend.pages.utils import INGIniousAuthPage


class TeamPage(INGIniousAuthPage):
    """ Team page """

    _logger = logging.getLogger("inginious.webapp.teams")

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """

        course = self.course_factory.get_course(courseid)
        username = self.user_manager.session_username()

        error = False
        change = False
        msg = ""
        data = web.input()
        if self.user_manager.has_staff_rights_on_course(course):
            raise web.notfound()
        elif not self.user_manager.course_is_open_to_user(course, lti=False):
            return self.template_helper.get_renderer().course_unavailable()
        elif "register_group" in data:
            change = True
            if course.can_students_choose_group():

                team = self.database.teams.find_one(
                    {"courseid": course.get_id(), "students": username})

                if team is not None:
                    team["students"].remove(username)
                    for index, group in enumerate(team["groups"]):
                        if username in group["students"]:
                            team["groups"][index]["students"].remove(username)
                    self.database.teams.replace_one({"courseid": course.get_id(), "students": username}, team)

                # Add student in the classroom and unique group
                self.database.teams.find_one_and_update({"_id": ObjectId(data["register_group"])},
                                                             {"$push": {"students": username}})
                new_team = self.database.teams.find_one_and_update({"_id": ObjectId(data["register_group"])},
                                                                             {"$push": {"groups.0.students": username}})

                if new_team is None:
                    error = True
                    msg = _("Couldn't register to the specified group.")
                else:
                    self._logger.info("User %s registered to team %s/%s", username, courseid, team["description"])
            else:
                error = True
                msg = _("You are not allowed to change group.")
        elif "unregister_group" in data:
            change = True
            if course.can_students_choose_group():
                team = self.database.teams.find_one({"courseid": course.get_id(), "students": username, "groups.students": username})
                if team is not None:
                    for index, group in enumerate(team["groups"]):
                        if username in group["students"]:
                            team["groups"][index]["students"].remove(username)
                    self.database.teams.replace_one({"courseid": course.get_id(), "students": username}, team)
                    self._logger.info("User %s unregistered from group/team %s/%s", username, courseid, team["description"])
                else:
                    error = True
                    msg = _("You're not registered in a group.")
            else:
                error = True
                msg = _("You are not allowed to change group.")

        tasks = course.get_tasks()
        last_submissions = self.submission_manager.get_user_last_submissions(5, {"courseid": courseid, "taskid": {"$in": list(tasks.keys())}})
        for submission in last_submissions:
            submission["taskname"] = tasks[submission['taskid']].get_name(self.user_manager.session_language())

        team = self.user_manager.get_course_user_team(course)
        teams = self.user_manager.get_course_teams(course)
        users = self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course))

        return self.template_helper.get_renderer().team(course, last_submissions, teams, users,
                                                            team, msg, error)
