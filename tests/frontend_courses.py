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
import common
import common.base
import frontend
import frontend.base
import frontend.custom
import frontend.custom.courses
import frontend.session
import frontend.submission_manager


class frontend_courses(unittest.TestCase):

    def setUp(self):
        # Droping database
        client = frontend.base.get_database().connection
        client.drop_database(common.base.INGIniousConfiguration.get('mongo_opt', {}).get('database', 'INGIniousTest'))
        # Init test session
        frontend.session.init(app, {'loggedin': True, 'username': "test", "realname": "Test", "email": "mail@test.com"})

    def test_completion_percentage(self):
        '''Tests completion percentage of a course'''
        print "\033[1m-> frontend-course: completion percentage\033[0m"
        c = frontend.custom.courses.FrontendCourse('test2')
        number = 3  # one task is not accessible
        t = common.tasks.Task(c, 'task1')

        # Launch a task
        sid = frontend.submission_manager.add_job(t, {"unittest": "Answer 1"})
        while not frontend.submission_manager.is_done(sid):
            time.sleep(1)

        # Assert completion percentage is 100/number percent
        assert int(c.get_user_completion_percentage()) == int(100 / number)

    def test_last_submissions(self):
        '''Tests lasts submissions '''
        print "\033[1m-> frontend-course: lasts submissions\033[0m"
        c = frontend.custom.courses.FrontendCourse('test2')
        t = common.tasks.Task(c, 'task1')

        # Launch a task
        sid = frontend.submission_manager.add_job(t, {"unittest": "Answer 1"})
        while not frontend.submission_manager.is_done(sid):
            time.sleep(1)

        subs = c.get_user_last_submissions()

        assert len(subs) == 1
        assert subs[0]['courseid'] == 'test2'
        assert subs[0]['taskid'] == 'task1'
        assert subs[0]['input']['unittest'] == 'Answer 1'

    def tearDown(self):
        pass

if __name__ == "__main__":
    if not common.base.INGIniousConfiguration.get('tests', {}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> frontend-courses: tests cannot be run remotely\033[0m"
