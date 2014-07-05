import web
from frontend.base import renderer
import frontend.user as User
from common.courses import Course

#Index page
class IndexPage:
    #Simply display the page
    def GET(self):
        if User.isLoggedIn():
            userInput = web.input();
            if "logoff" in userInput:
                User.disconnect();
                return renderer.index(False)
            else:
                return renderer.main(Course.GetAllCoursesIds())
        else:
            return renderer.index(False)
    #Try to log in
    def POST(self):
        userInput = web.input();
        if "login" in userInput and "password" in userInput and User.connect(userInput.login,userInput.password):
            return renderer.main(Course.GetAllCoursesIds())
        else:
            return renderer.index(True)