""" Course page """
import web

from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
from frontend.custom.tasks import FrontendTask
import frontend.user as User
# Course page


class CoursePage(object):

    """ Course page """

    def GET(self, courseid):
        """ GET request """

        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if not course.is_open() and User.get_username() not in course.get_admins():
                    return renderer.course_unavailable()

                User.get_data().view_course(courseid)
                last_submissions = course.get_user_last_submissions()
                except_free_last_submissions = []
                for submission in last_submissions:
                    try:
                        submission["task"] = course.get_task(submission['taskid'])
                        except_free_last_submissions.append(submission)
                    except:
                        pass
                return renderer.course(course, except_free_last_submissions)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
