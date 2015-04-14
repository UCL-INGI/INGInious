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
import time

from tests import *
import frontend
import frontend.base
import frontend.custom
import frontend.custom.courses
import frontend.custom.tasks
import frontend.session
import frontend.submission_manager
class frontend_tasks(unittest.TestCase):
    def setUp(self):
        # Droping database
        client = frontend.base.get_database().connection
        client.drop_database(frontend.configuration.INGIniousConfiguration.get('mongo_opt', {}).get('database', 'INGIniousTest'))
        #Init test session
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
    
    def test_user_status(self):
        '''Tests user status '''
        print "\033[1m-> frontend-tasks: user task status\033[0m"
        c = frontend.custom.courses.FrontendCourse('test2')
        number = len(c.get_tasks())
        t = frontend.custom.tasks.FrontendTask(c, 'task1')
        
        assert t.get_user_status() == 'notviewed'
        
        #Launch a task
        sid = frontend.submission_manager.add_job(t, {"unittest":"Answer 1"})
        while not frontend.submission_manager.is_done(sid):
            time.sleep(1)
        
        assert t.get_user_status() == 'succeeded'
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not frontend.configuration.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> frontend-tasks: tests cannot be run remotely\033[0m"
