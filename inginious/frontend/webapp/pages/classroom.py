# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """

import web
from bson.objectid import ObjectId

from inginious.frontend.webapp.pages.utils import INGIniousPage


class ClassroomPage(INGIniousPage):
    """ Classroom page """

    def GET(self, courseid):
        """ GET request """

        if not self.user_manager.session_logged_in():
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_fields(), False)

        course = self.course_factory.get_course(courseid)
        username = self.user_manager.session_username()

        error = False
        msg = ""
        data = web.input()
        if self.user_manager.has_staff_rights_on_course(course):
            raise web.notfound()
        elif not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().course_unavailable()
        elif "register_group" in data:
            if course.can_students_choose_group() and course.use_classrooms():
                classroom = self.database.classrooms.find_one({"courseid": course.get_id(), "students": username})

                if int(data["register_group"]) >= 0 and (len(classroom["groups"]) > int(data["register_group"])):
                    group = classroom["groups"][int(data["register_group"])]
                    if group["size"] > len(group["students"]):
                        for index, group in enumerate(classroom["groups"]):
                            if username in group["students"]:
                                classroom["groups"][index]["students"].remove(username)
                        classroom["groups"][int(data["register_group"])]["students"].append(username)
                    self.database.classrooms.replace_one({"courseid": course.get_id(), "students": username}, classroom)
                else:
                    error = True
                    msg = "Couldn't register to the specified group."
            elif course.can_students_choose_group():

                classroom = self.database.classrooms.find_one(
                    {"courseid": course.get_id(), "students": username})

                if classroom is not None:
                    classroom["students"].remove(username)
                    for index, group in enumerate(classroom["groups"]):
                        if username in group["students"]:
                            classroom["groups"][index]["students"].remove(username)
                    self.database.classrooms.replace_one({"courseid": course.get_id(), "students": username}, classroom)

                # Add student in the classroom and unique group
                self.database.classrooms.find_one_and_update({"_id": ObjectId(data["register_group"])},
                                                             {"$push": {"students": username}})
                new_classroom = self.database.classrooms.find_one_and_update({"_id": ObjectId(data["register_group"])},
                                                                             {"$push": {"groups.0.students": username}})

                if new_classroom is None:
                    error = True
                    msg = "Couldn't register to the specified group."
            else:
                error = True
                msg = "You are not allowed to change group."
        elif "unregister_group" in data:
            if course.can_students_choose_group():
                classroom = self.database.classrooms.find_one({"courseid": course.get_id(), "students": username, "groups.students": username})
                if classroom is not None:
                    for index, group in enumerate(classroom["groups"]):
                        if username in group["students"]:
                            classroom["groups"][index]["students"].remove(username)
                    self.database.classrooms.replace_one({"courseid": course.get_id(), "students": username}, classroom)
                else:
                    error = True
                    msg = "You're not registered in a group."
            else:
                error = True
                msg = "You are not allowed to change group."

        last_submissions = self.submission_manager.get_user_last_submissions_for_course(course, one_per_task=True)
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = course.get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass

        classroom = self.user_manager.get_course_user_classroom(course)
        classrooms = list(self.database.classrooms.find({"courseid": course.get_id()}))
        users = self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course))

        if course.use_classrooms():
            mygroup = None
            for index, group in enumerate(classroom["groups"]):
                if self.user_manager.session_username() in group["students"]:
                    mygroup = group
                    mygroup["index"] = index + 1

            return self.template_helper.get_renderer().classroom(course, except_free_last_submissions, classroom, users, mygroup, msg, error)
        else:
            return self.template_helper.get_renderer().group(course, except_free_last_submissions, classrooms, users,
                                                             classroom, msg, error)