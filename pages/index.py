import web
from common.base import renderer
import frontend.login as Login
from common.courses import Course

#Index page
class IndexPage:
    #Simply display the page
    def GET(self):
        if Login.isLoggedIn():
            userInput = web.input();
            if "logoff" in userInput:
                Login.disconnect();
                return renderer.index(False)
            else:
                return renderer.main(Course.GetAllCoursesIds())
        else:
            return renderer.index(False)
    #Try to log in
    def POST(self):
        userInput = web.input();
        if "login" in userInput and "password" in userInput and Login.connect(userInput.login,userInput.password):
            return renderer.main(Course.GetAllCoursesIds())
        else:
            return renderer.index(True)