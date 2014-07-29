import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base
from tests import *

class web_login_session(unittest.TestCase):
    def setUp(self):
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        
    def test_init(self):
        '''Tests if home page loads with a connected user'''
        print "\033[1m-> web-login: index response when connected\033[0m"
        resp = appt.get('/')
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Log off')
    
    def test_logout(self):
        '''Tests if logout works'''
        print "\033[1m-> web-login: logout\033[0m"
        resp = appt.get('/index?logoff')
        self.assertEqual(resp.status_int, 200)
        resp.mustcontain('Log in')
    
    def tearDown(self):
        pass

class web_login_nosession(unittest.TestCase):
    def setUp(self):
        
        # Loads tests credentials from config file
        self.wrong_username = common.base.INGIniousConfiguration['tests']['wrong_username']
        self.wrong_password = common.base.INGIniousConfiguration['tests']['wrong_password']
        self.correct_username = common.base.INGIniousConfiguration['tests']['correct_username']
        self.correct_password = common.base.INGIniousConfiguration['tests']['correct_password']
        frontend.session.init(app, {'loggedin':False}) 
        
    def test_init(self):
        '''Tests if home page gives response and invites user to log'''
        print "\033[1m-> web-login: index response when not connected\033[0m"
        resp = appt.get('/')
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Log in')
    
    def test_correct_login(self):
        '''Tests if correct credentials leads to a logged user page'''
        print "\033[1m-> web-login: correct login\033[0m"
        resp = appt.get('/')
        form = resp.forms[0]
        form['login'] = self.correct_username
        form['password'] = self.correct_password
        resp = form.submit()
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Log off')
        
    def test_wrong_login(self):
        '''Tests if wrong credentials leads to the home page with login'''
        print "\033[1m-> web-login: incorrect login\033[0m"
        resp = appt.get('/')
        form = resp.forms[0]
        form['login'] = self.wrong_username
        form['password'] = self.wrong_password
        resp = form.submit()
        self.assertEqual(resp.status_int,200)
        self.assertEqual(frontend.user.is_logged_in(), False)
        resp.mustcontain('Invalid login/password')
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
