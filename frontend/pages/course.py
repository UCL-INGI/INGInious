from common.courses import Course
from frontend.base import renderer
import frontend.user as User
import web

#Course page
class CoursePage:
    #Simply display the page
    def GET(self,courseId):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                return renderer.course(course)
            except:
                raise web.notfound()
        else:
            return renderer.index(False)