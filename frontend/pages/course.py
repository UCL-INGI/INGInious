import web

from common.courses import Course
from common.tasks import Task
from frontend.base import renderer
import frontend.user as User


# Course page
class CoursePage:
    # Simply display the page
    def GET(self, courseId):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                lastSubmissions=course.getUserLastSubmissions()
                exceptFreeLastSubmissions = []
                for submission in lastSubmissions:
                    try:
                        submission["task"] = Task(submission['courseId'],submission['taskId'])
                        exceptFreeLastSubmissions.append(submission)
                    except:
                        pass
                return renderer.course(course,exceptFreeLastSubmissions)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)