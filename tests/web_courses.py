# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
import unittest

import webtest

from tests import *
import app_frontend
import inginious.common.base
import inginious.frontend
import inginious.frontend.session
class web_courses(unittest.TestCase):
    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        
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
        inginious.frontend.session.init(app, {'loggedin':True, 'username':"testadmin2", "realname":"Test", "email":"mail@test.com"})
        resp = appt.get('/course/test')
        resp.mustcontain('Statistics') #testadmin2 is an admin
        resp = appt.get('/course/test2')
        assert 'Manage' not in resp # testadmin2 is not an admin
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> web-courses: tests cannot be run remotely\033[0m"
