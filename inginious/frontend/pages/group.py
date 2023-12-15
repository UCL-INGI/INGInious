# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """

import logging

import flask
from werkzeug.exceptions import Forbidden
from bson.objectid import ObjectId

from inginious.frontend.pages.utils import INGIniousAuthPage


class GroupPage(INGIniousAuthPage):
    """ Group page """

    _logger = logging.getLogger("inginious.webapp.groups")

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """

        course = self.taskset_factory.get_course(courseid)
        username = self.user_manager.session_username()

        error = False
        msg = ""
        data = flask.request.args
        if self.user_manager.has_admin_rights_on_course(course):
            raise Forbidden(description=_("You can't access this page as a member of the staff."))
        elif not (self.user_manager.course_is_open_to_user(course, lti=False)
                  and self.user_manager.course_is_user_registered(course, username)):
            return self.template_helper.render("course_unavailable.html")
        elif "register_group" in data:
            if course.can_students_choose_group():

                group = self.database.groups.find_one(
                    {"courseid": course.get_id(), "students": username})
                if group is not None:
                    group["students"].remove(username)
                    self.database.groups.replace_one({"courseid": course.get_id(), "students": username}, group)

                # Add student in the audience and unique group if group is not full
                new_group = self.database.groups.find_one_and_update(
                    {"_id": ObjectId(data["register_group"]),
                     "$where": "this.students.length<this.size"},
                    {"$push": {"students": username}})

                if new_group is None:
                    error = True
                    msg = _("Couldn't register to the specified group.")
                else:
                    self._logger.info("User %s registered to group %s/%s", username, courseid, new_group["description"])
            else:
                error = True
                msg = _("You are not allowed to change group.")
        elif "unregister_group" in data:
            if course.can_students_choose_group():
                group = self.database.groups.find_one({"courseid": course.get_id(), "students": username})
                if group is not None:
                    self.database.groups.find_one_and_update({"_id": group["_id"]}, {"$pull": {"students": username}})
                    self._logger.info("User %s unregistered from group %s/%s", username, courseid, group["description"])
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

        user_group = self.user_manager.get_course_user_group(course)
        user_audiences = [audience["_id"] for audience in self.database.audiences.find({"courseid": courseid, "students": username})]
        groups = self.user_manager.get_course_groups(course)

        student_allowed_in_group = lambda group: any(set(user_audiences).intersection(group["audiences"])) or not group["audiences"]
        allowed_groups = [group for group in groups if student_allowed_in_group(group)]

        users = self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course))

        return self.template_helper.render("group.html",
                                           course=course,
                                           submissions=last_submissions,
                                           allowed_groups=allowed_groups,
                                           groups=groups,
                                           users=users,
                                           mygroup=user_group,
                                           msg=msg,
                                           error=error)
