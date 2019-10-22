# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web
from bson.objectid import ObjectId

import inginious.common.custom_yaml as yaml
from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseTeamListPage(INGIniousAdminPage):
    """ Course administration page: list of teams """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        if course.is_lti():
            raise web.notfound()

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="teams.yaml"', unique=True)
            teams = [{"description": team["description"],
                           "groups": team["groups"],
                           "students": team["students"],
                           "tutors": team["tutors"]} for team in
                          self.user_manager.get_course_teams(course) if len(team["groups"]) > 0]

            return yaml.dump(teams)

        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)

        if course.is_lti():
            raise web.notfound()

        error = False
        try:
            if self.user_manager.has_admin_rights_on_course(course):
                data = web.input()
                if 'classroom' in data:
                    self.database.teams.insert({"courseid": courseid, "students": [],
                                                     "tutors": [], "groups": [],
                                                     "description": data['classroom']})
                    msg = _("New classroom created.")
                else:  # default, but with no classroom detected
                    msg = _("Invalid classroom selected.")
            else:
                msg = _("You have no rights to add/change classrooms")
                error = True
        except:
            msg = _('User returned an invalid form.')
            error = True

        return self.page(course, msg, error)

    def submission_url_generator(self, teamid):
        """ Generates a submission url """
        return "?format=taskid%2Fteam&teams=" + str(teamid)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        teams = OrderedDict()
        taskids = list(course.get_tasks().keys())

        for team in self.user_manager.get_course_teams(course):
            teams[team['_id']] = dict(list(team.items()) +
                                                [("tried", 0),
                                                 ("done", 0),
                                                 ("url", self.submission_url_generator(team['_id']))
                                                 ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": taskids},
                                "username": {"$in": team["students"]}
                            }
                    },
                    {
                        "$group":
                            {
                                "_id": "$taskid",
                                "tried": {"$sum": 1},
                                "done": {"$sum": {"$cond": [{"$eq": ["$result", "success"]}, 1, 0]}}
                            }
                    },

                ]))

            for c in data:
                teams[team['_id']]["tried"] += 1 if c["tried"] else 0
                teams[team['_id']]["done"] += 1 if c["done"] else 0

        my_teams, other_teams = [], []
        for team in teams.values():
            if self.user_manager.session_username() in team["tutors"]:
                my_teams.append(team)
            else:
                other_teams.append(team)

        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.team_list(course, [my_teams, other_teams], msg, error)
