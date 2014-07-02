from modules.session import sessionManager

#Allow to login, logout and get informations about the current logged-in user.
class Login:
    def getUsername(self):
        if not self.isLoggedIn():
            return None
        return sessionManager.get().username
    def isLoggedIn(self):
        return "loggedin" in sessionManager.get() and sessionManager.get().loggedin
    def disconnect(self):
        sessionManager.get().loggedin = False
        sessionManager.get().username = None
        sessionManager.get().realname = None
        sessionManager.get().email = None
        return
    def connect(self, login, password):
        if login == "test" and password == "test":
            sessionManager.get().loggedin = True
            sessionManager.get().username = "test"
            sessionManager.get().realname = "Pythia User"
            sessionManager.get().email = "pythia.user@student.uclouvain.be"
            return True
        else:
            return False
        
#Login class should be a singleton. loginInstance should be called from the outside of the module
loginInstance = Login()