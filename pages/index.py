import web
from modules.base import renderer
from modules.login import loginInstance

#Index page
class IndexPage:
    #Simply display the page
    def GET(self):
        return renderer.index(False)
    #Try to log in
    def POST(self):
        userInput = web.input();
        if "login" in userInput and "password" in userInput and loginInstance.connect(userInput.login,userInput.password):
            return renderer.index(False)
        else:
            return renderer.index(True)