# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from collections import OrderedDict

import web
from bson.objectid import ObjectId

import inginious.common.custom_yaml as yaml
from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage


class CourseAudienceListPage(INGIniousAdminPage):
    """ Course administration page: list of audiences """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        if "download" in web.input():
            web.header('Content-Type', 'text/x-yaml', unique=True)
            web.header('Content-Disposition', 'attachment; filename="audiences.yaml"', unique=True)
            audiences = [{"description": audience["description"],
                           "students": audience["students"],
                           "tutors": audience["tutors"]} for audience in
                          self.user_manager.get_course_audiences(course)]

            return yaml.dump(audiences)

        return self.page(course)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)

        error = False
        try:
            if self.user_manager.has_admin_rights_on_course(course):
                data = web.input()
                if 'audience' in data:
                    self.database.audiences.insert({"courseid": courseid, "students": [],
                                                     "tutors": [],
                                                     "description": data['audience']})
                    msg = _("New audience created.")
                else:  # default, but with no audience detected
                    msg = _("Invalid audience selected.")
            else:
                msg = _("You have no rights to add/change audiences")
                error = True
        except:
            msg = _('User returned an invalid form.')
            error = True

        return self.page(course, msg, error)

    def submission_url_generator(self, audienceid):
        """ Generates a submission url """
        return "?format=taskid%2Faudience&audiences=" + str(audienceid)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        audiences = OrderedDict()
        taskids = list(course.get_tasks().keys())

        for audience in self.user_manager.get_course_audiences(course):
            audiences[audience['_id']] = dict(list(audience.items()) +
                                                [("tried", 0),
                                                 ("done", 0),
                                                 ("url", self.submission_url_generator(audience['_id']))
                                                 ])

            data = list(self.database.submissions.aggregate(
                [
                    {
                        "$match":
                            {
                                "courseid": course.get_id(),
                                "taskid": {"$in": taskids},
                                "username": {"$in": audience["students"]}
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
                audiences[audience['_id']]["tried"] += 1 if c["tried"] else 0
                audiences[audience['_id']]["done"] += 1 if c["done"] else 0

        my_audiences, other_audiences = [], []
        for audience in audiences.values():
            if self.user_manager.session_username() in audience["tutors"]:
                my_audiences.append(audience)
            else:
                other_audiences.append(audience)

        if "csv" in web.input():
            return make_csv(data)

        return self.template_helper.get_renderer().course_admin.audience_list(course, [my_audiences, other_audiences], msg, error)
