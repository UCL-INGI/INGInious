import web

from common.courses import Course
from frontend.base import renderer
import frontend.user as User
from frontend.submission_manager import getUserLastSubmissions

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
                return self.callMain()
        else:
            return renderer.index(False)
    #Try to log in
    def POST(self):
        userInput = web.input();
        if "login" in userInput and "password" in userInput and User.connect(userInput.login,userInput.password):
            return self.callMain()
        else:
            return renderer.index(True)
    def callMain(self):
        return renderer.main(Course.GetAllCourses(),getUserLastSubmissions({},5))