from frontend.base import renderer
import frontend.user as User
from common.courses import Course

#Course page
class CoursePage:
    #Simply display the page
    def GET(self,courseId):
        if User.isLoggedIn():
            #try: #TODO:enable
                course = Course(courseId)
                return renderer.course(course)
            #except:
            #    return renderer.error404()
        else:
            return renderer.index(False)