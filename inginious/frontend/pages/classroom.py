# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """

import logging

import web
from bson.objectid import ObjectId

from inginious.frontend.pages.utils import INGIniousAuthPage


class ClassroomPage(INGIniousAuthPage):
    """ Classroom page """

    _logger = logging.getLogger("inginious.webapp.classrooms")

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
                classroom = self.database.classrooms.find_one({"courseid": course.get_id(), "students": username})

                if int(data["register_group"]) >= 0 and (len(classroom["groups"]) > int(data["register_group"])):
                    group = classroom["groups"][int(data["register_group"])]
                    if group["size"] > len(group["students"]):
                        for index, group in enumerate(classroom["groups"]):
                            if username in group["students"]:
                                classroom["groups"][index]["students"].remove(username)
                        classroom["groups"][int(data["register_group"])]["students"].append(username)
                    self.database.classrooms.replace_one({"courseid": course.get_id(), "students": username}, classroom)
                    self._logger.info("User %s registered to group %s/%s/%s", username, courseid, classroom["description"], data["register_group"])
                else:
                    error = True
                    msg = _("Couldn't register to the specified group.")
            else:
                error = True
                msg = _("You are not allowed to change group.")
        elif "unregister_group" in data:
            change = True
            if course.can_students_choose_group():
                classroom = self.database.classrooms.find_one({"courseid": course.get_id(), "students": username, "groups.students": username})
                if classroom is not None:
                    for index, group in enumerate(classroom["groups"]):
                        if username in group["students"]:
                            classroom["groups"][index]["students"].remove(username)
                    self.database.classrooms.replace_one({"courseid": course.get_id(), "students": username}, classroom)
                    self._logger.info("User %s unregistered from group/team %s/%s", username, courseid, classroom["description"])
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

        classroom = self.user_manager.get_course_user_classroom(course)
        classrooms = self.user_manager.get_course_classrooms(course)
        users = self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course))

        mygroup = None
        if classroom:
            for index, group in enumerate(classroom["groups"]):
                if self.user_manager.session_username() in group["students"]:
                    mygroup = group
                    mygroup["index"] = index + 1

        return self.template_helper.get_renderer().classroom(course, last_submissions, classroom, users,
                                                             mygroup, msg, error, change)
