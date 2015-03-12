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
import time
import unittest

from pymongo import MongoClient
import webtest

from tests import *
import app_frontend
import inginious.common
import inginious.common.base
import inginious.frontend
import inginious.frontend.base
import inginious.frontend.custom
import inginious.frontend.custom.courses
import inginious.frontend.custom.tasks
import inginious.frontend.session
import inginious.frontend.submission_manager
class frontend_tasks(unittest.TestCase):
    def setUp(self):
        # Droping database
        client = inginious.frontend.base.get_database().connection
        client.drop_database(inginious.common.base.INGIniousConfiguration.get('mongo_opt', {}).get('database', 'INGIniousTest'))
        #Init test session
        inginious.frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
    
    def test_user_status(self):
        '''Tests user status '''
        print "\033[1m-> inginious.frontend-tasks: user task status\033[0m"
        c = inginious.frontend.custom.courses.FrontendCourse('test2')
        number = len(c.get_tasks())
        t = inginious.frontend.custom.tasks.FrontendTask(c, 'task1')
        
        assert t.get_user_status() == 'notviewed'
        
        #Launch a task
        sid = inginious.frontend.submission_manager.add_job(t, {"unittest":"Answer 1"})
        while not inginious.frontend.submission_manager.is_done(sid):
            time.sleep(1)
        
        assert t.get_user_status() == 'succeeded'
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> inginious.frontend-tasks: tests cannot be run remotely\033[0m"
