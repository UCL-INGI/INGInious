# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """
import web

from inginious.frontend.webapp.pages.utils import INGIniousAuthPage


class CoursePage(INGIniousAuthPage):
    """ Course page """

    def get_course(self, courseid):
        """ Return the course """
        try:
            course = self.course_factory.get_course(courseid)
        except:
            raise web.notfound()

        return course

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course = self.get_course(courseid)

        user_input = web.input()
        if "unregister" in user_input and course.allow_unregister():
            self.user_manager.course_unregister_user(course, self.user_manager.session_username())
            raise web.seeother(self.app.get_homepath() + '/index')

        return self.show_page(course)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course = self.get_course(courseid)
        return self.show_page(course)

    def show_page(self, course):
        """ Prepares and shows the course page """
        username = self.user_manager.session_username()
        if not self.user_manager.course_is_open_to_user(course, lti=False):
            return self.template_helper.get_renderer().course_unavailable()
        else:
            tasks = course.get_tasks()
            last_submissions = self.submission_manager.get_user_last_submissions(5, {"courseid": course.get_id(), "taskid": {"$in": list(tasks.keys())}})

            for submission in last_submissions:
                    submission["taskname"] = tasks[submission['taskid']].get_name()

            tasks_data = {}
            user_tasks = self.database.user_tasks.find({"username": username, "courseid": course.get_id(), "taskid": {"$in": list(tasks.keys())}})
            is_admin = self.user_manager.has_staff_rights_on_course(course, username)

            tasks_score = [0.0, 0.0]

            for taskid, task in tasks.items():
                tasks_data[taskid] = {"visible": task.get_accessible_time().after_start() or is_admin, "succeeded": False,
                                      "grade": 0.0}
                tasks_score[1] += task.get_grading_weight() if tasks_data[taskid]["visible"] else 0

            for user_task in user_tasks:
                tasks_data[user_task["taskid"]]["succeeded"] = user_task["succeeded"]
                tasks_data[user_task["taskid"]]["grade"] = user_task["grade"]

                weighted_score = user_task["grade"]*tasks[user_task["taskid"]].get_grading_weight()
                tasks_score[0] += weighted_score if tasks_data[user_task["taskid"]]["visible"] else 0

            course_grade = round(tasks_score[0]/tasks_score[1]) if tasks_score[1] > 0 else 0

            return self.template_helper.get_renderer().course(course, last_submissions, tasks, tasks_data, course_grade)
