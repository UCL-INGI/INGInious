# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Index page """
import flask
from collections import OrderedDict

from inginious.frontend.pages.utils import INGIniousAuthPage


class MyCoursesPage(INGIniousAuthPage):
    """ Index page """

    def GET_AUTH(self):  # pylint: disable=arguments-differ
        """  Display main course list page """
        username = self.user_manager.session_username()
        user_info = self.user_manager.get_user_info(username)

        all_courses = self.course_factory.get_all_courses()

        # Display
        open_courses = {courseid: course for courseid, course in all_courses.items()
                        if self.user_manager.course_is_open_to_user(course, username, False) and
                        self.user_manager.course_is_user_registered(course, username)}
        open_courses = OrderedDict(sorted(iter(open_courses.items()), key=lambda x: x[1].get_name(self.user_manager.session_language())))

        last_submissions = self.submission_manager.get_user_last_submissions(5, {"courseid": {"$in": list(open_courses.keys())}})
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = open_courses[submission['courseid']].get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass

        registerable_courses = {courseid: course for courseid, course in all_courses.items() if
                                not self.user_manager.course_is_user_registered(course, username) and
                                course.is_registration_possible(user_info)}

        registerable_courses = OrderedDict(sorted(iter(registerable_courses.items()), key=lambda x: x[1].get_name(self.user_manager.session_language())))

        return self.template_helper.render("mycourses.html",
                                           open_courses=open_courses,
                                           registrable_courses=registerable_courses,
                                           submissions=except_free_last_submissions)
