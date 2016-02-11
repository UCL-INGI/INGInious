# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Course page """
import web

from inginious.frontend.webapp.pages.utils import INGIniousPage


class CoursePage(INGIniousPage):
    """ Course page """

    def GET(self, courseid):
        """ GET request """

        if self.user_manager.session_logged_in():
            try:
                course = self.course_factory.get_course(courseid)
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
            except web.seeother:
                raise
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_fields(), False)
