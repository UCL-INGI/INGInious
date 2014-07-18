""" Index page """
import web

from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
from frontend.submission_manager import get_user_last_submissions
import frontend.user as User


class IndexPage(object):

    """ Index page """

    def GET(self):
        """ GET request """
        if User.is_logged_in():
            user_input = web.input()
            if "logoff" in user_input:
                User.disconnect()
                return renderer.index(False)
            else:
                return self.call_main()
        else:
            return renderer.index(False)

    def POST(self):
        """ POST request: login """
        user_input = web.input()
        if "login" in user_input and "password" in user_input and User.connect(user_input.login, user_input.password):
            return self.call_main()
        else:
            return renderer.index(True)

    def call_main(self):
        """ Display main page (only when logged) """
        last_submissions = get_user_last_submissions({}, 5)
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = FrontendCourse(submission['courseid']).get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass
        courses = {courseid: course for courseid, course in FrontendCourse.get_all_courses().iteritems() if course.is_open() or User.get_username() in course.get_admins()}
        return renderer.main(courses, except_free_last_submissions)
