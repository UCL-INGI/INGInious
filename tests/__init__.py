from nose.tools import *
from paste.fixture import TestApp
import web
import frontend.session
import frontend.user
import common.base

common.base.pythiaConfiguration["tasksDirectory"] = "tests/tasks/"

def nosessioninit(app):
    if web.config.get('_session') is None:
        frontend.session.session = web.session.Session(app, web.session.DiskStore('sessionstest'), {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        web.config._session = frontend.session.session
    else:
        frontend.session.session = web.config._session
frontend.session.init = nosessioninit

def getUsername():
    return "Test"
frontend.user.getUsername = getUsername

def getRealname():
    return "Test"
frontend.user.getRealname = getRealname

def isLoggedIn():
    return True
frontend.user.isLoggedIn = isLoggedIn

def disconnect():
    return
frontend.user.disconnect = disconnect

def connect(login, password):
    return
frontend.user.connect = connect

import app_frontend