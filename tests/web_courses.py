import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base
from tests import *

class web_courses(unittest.TestCase):
    def setUp(self):
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        
    def test_course_list(self):
        '''Tests if the course list is correct'''
        print "\033[1m-> web-courses: course list\033[0m"
        resp = appt.get('/index')
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Unit test 1') # Accessibility : null
        resp.mustcontain('Unit test 2') # Accessibility : 1970-2033
        assert 'Unit test 3' not in resp # Accessibility : 1970-1970
    
    def test_course_admin(self):
        '''Tests accessibility to course administration'''
        print "\033[1m-> web-courses: course administration link visibility\033[0m"
        frontend.session.init(app, {'loggedin':True, 'username':"testadmin2", "realname":"Test", "email":"mail@test.com"})
        resp = appt.get('/course/test')
        resp.mustcontain('Statistics') #testadmin2 is an admin
        resp = appt.get('/course/test2')
        assert 'Manage' not in resp # testadmin2 is not an admin
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> web-courses: tests cannot be run remotely\033[0m"
