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
import json
import time
import unittest

import webtest

from tests import *
import app_frontend
import inginious.common.base
import inginious.frontend
import inginious.frontend.session
class web_tasks(unittest.TestCase):
    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        
    def test_basic_tasks_list(self):
        '''Tests if a basic course list is correct'''
        print "\033[1m-> web-tasks: course tasks list\033[0m"
        resp = appt.get('/course/test')
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Task 1')
        resp.mustcontain('Task 2')
        resp.mustcontain('Task 3')
        resp.mustcontain('Task 4')
    
    def test_decimal_rendering(self):
        '''Tests rendering of a decimal question '''
        print "\033[1m-> web-tasks: decimal-input task rendering\033[0m"
        resp = appt.get('/course/test/task1')
        resp.mustcontain('Header 1')
        resp.mustcontain('input type="number" name="unittest/decimal')
        resp.mustcontain('Here should go some introductory text.')
    
    def test_integer_rendering(self):
        '''Tests rendering of a decimal question '''
        print "\033[1m-> web-tasks: integer-input task rendering\033[0m"
        resp = appt.get('/course/test/task2')
        resp.mustcontain('Question 2')
        resp.mustcontain('Header 2')
        resp.mustcontain('input type="number" name="unittest/int')
        resp.mustcontain('Here should go some introductory text.')
    
    def test_multichoice_rendering(self):
        '''Tests rendering of a multichoice question '''
        print "\033[1m-> web-tasks: multichoice-input task rendering\033[0m"
        resp = appt.get('/course/test/task3')
        resp.mustcontain('Question 3')
        resp.mustcontain('Header 3')
        resp.mustcontain('type="checkbox" name="unittest"')
        form = resp.form
        
        #Check the values of checkbox are logic
        values = ['0', '1', '2', '3']
        form['unittest'] = values
        self.assertIn(form.get('unittest', index=0).value, values)
        self.assertIn(form.get('unittest', index=1).value, values)
        self.assertIn(form.get('unittest', index=2).value, values)
        
        resp.mustcontain('Choice 1') # Choices are valid
        resp.mustcontain('Choice 2')
        resp.mustcontain('Here should go some introductory text.')
    
    def test_multiline_rendering(self):
        '''Tests rendering of a multiline code question '''
        print "\033[1m-> web-tasks: multiline-input task rendering\033[0m"
        resp = appt.get('/course/test/task4')
        resp.mustcontain('Question 4')
        resp.mustcontain('Header 4')
        resp.mustcontain('div id="unittest" class="aceEditor"')
    
    def test_accessibility(self):
        '''Tests accessibility of different tasks '''
        print "\033[1m-> web-tasks: task accessibility\033[0m"
        resp = appt.get('/course/test2')
        resp.mustcontain('Task 1')
        resp.mustcontain('Task 3') # 1970 - 2033
        resp.mustcontain('Task 2 (task currently unavailable)') # Accesibility 1970-1970
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> web-tasks: tests cannot be run remotely\033[0m"
