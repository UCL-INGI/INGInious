import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base
from tests import *

class frontend_course_display(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> frontend_course_display:setUp\033[0m"
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        
    def test_course_list(self):
        '''Tests if the course list is correct'''
        resp = appt.get('/index')
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Unit test 1') # Accessibility : null
        resp.mustcontain('Unit test 2') # Accessibility : 1970-2033
        assert 'Unit test 3' not in resp # Accessibility : 1970-1970
    
    def test_course_admin(self):
        '''Tests accessibility to course administration'''
        frontend.session.init(app, {'loggedin':True, 'username':"testadmin2", "realname":"Test", "email":"mail@test.com"})
        resp = appt.get('/course/test')
        resp.mustcontain('Statistics') #testadmin2 is an admin
        resp = appt.get('/course/test2')
        assert 'Manage' not in resp # testadmin2 is not an admin
    
    def tearDown(self):
        print "\033[1m-> frontend_course_display:tearDown\033[0m"

if __name__ == "__main__":
    unittest.main()
