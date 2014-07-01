#Allow to login, logout and get informations about the current logged-in user.
class Login:
    def getUsername(self):
        return None
    def isLoggedIn(self):
        return False
    def disconnect(self):
        return
    def connect(self, login, password):
        return False
loginInstance = Login()