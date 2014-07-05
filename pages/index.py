import web
from common.base import renderer
from frontend.login import loginInstance
from common.courses import Course

#Index page
class IndexPage:
    #Simply display the page
    def GET(self):
        if loginInstance.isLoggedIn():
            userInput = web.input();
            if "logoff" in userInput:
                loginInstance.disconnect();
                return renderer.index(False)
            else:
                return renderer.main(Course.GetAllCoursesIds())
        else:
            return renderer.index(False)
    #Try to log in
    def POST(self):
        userInput = web.input();
        if "login" in userInput and "password" in userInput and loginInstance.connect(userInput.login,userInput.password):
            return renderer.main(Course.GetAllCoursesIds())
        else:
            return renderer.index(True)