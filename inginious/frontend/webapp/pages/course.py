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
            raise web.seeother('/index')

        return self.show_page(course)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course = self.get_course(courseid)
        return self.show_page(course)

    def show_page(self, course):
        """ Prepares and shows the course page """
        if not self.user_manager.course_is_open_to_user(course):
            return self.template_helper.get_renderer().course_unavailable()
        else:
            last_submissions = self.submission_manager.get_user_last_submissions_for_course(course, one_per_task=True)
            except_free_last_submissions = []
            for submission in last_submissions:
                try:
                    submission["task"] = course.get_task(submission['taskid'])
                    except_free_last_submissions.append(submission)
                except:
                    pass

            return self.template_helper.get_renderer().course(course, except_free_last_submissions)
