# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
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
import common.base
import frontend
import frontend.session
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
        self.wrong_username = frontend.configuration.INGIniousConfiguration['tests']['wrong_username']
        self.wrong_password = frontend.configuration.INGIniousConfiguration['tests']['wrong_password']
        self.correct_username = frontend.configuration.INGIniousConfiguration['tests']['correct_username']
        self.correct_password = frontend.configuration.INGIniousConfiguration['tests']['correct_password']
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
    if not frontend.configuration.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> web-login: tests cannot be run remotely\033[0m"
