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

import app_frontend
import inginious.common.base
import inginious.frontend
import inginious.frontend.session
from tests import *
import webtest


class web_admin_access(unittest.TestCase):

    def setUp(self):
        pass

    def test_no_access(self):
        '''Tests if access isn't granted to an unauthorized user'''
        print "\033[1m-> web-admin: authorized administration page access\033[0m"
        inginious.frontend.session.init(app, {'loggedin': True, 'username': "testadmin2", "realname": "Test", "email": "mail@test.com"})
        resp = appt.get('/admin/test2', status="*")
        self.assertEqual(resp.status_int, 404)

    def test_access(self):
        '''Tests if access is granted to an authorized user'''
        print "\033[1m-> web-admin: unauthorized administration page access\033[0m"
        inginious.frontend.session.init(app, {'loggedin': True, 'username': "testadmin1", "realname": "Test", "email": "mail@test.com"})
        resp = appt.get('/admin/test2', status="*")
        self.assertEqual(resp.status_int, 200)

    def tearDown(self):
        pass


class web_admin_views(unittest.TestCase):

    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin': True, 'username': "testadmin1", "realname": "Test", "email": "mail@test.com"})

    def test_course_student_view(self):
        '''Tests if student view displays correctly'''
        print "\033[1m-> web-admin: course students list view\033[0m"
        resp = appt.get('/admin/test')
        resp.mustcontain('Download all submissions')
        resp.mustcontain('CSV')
        resp.mustcontain('Download submissions')
        resp.mustcontain('View')

    def test_course_task_view(self):
        '''Tests if task view display correctly'''
        print "\033[1m-> web-admin: course tasks view\033[0m"
        resp = appt.get('/admin/test/tasks')
        resp.mustcontain('Task 1')
        resp.mustcontain('Task 2')
        resp.mustcontain('Task 3')
        resp.mustcontain('Task 4')

    def test_course_download(self):
        '''Tests if downloading all course submissions returns a tarfile'''
        print "\033[1m-> web-admin: course tarfile download\033[0m"
        resp = appt.get('/admin/test/submissions?dl=course')
        self.assertEquals(resp.content_type, 'application/x-gzip')
        resp = appt.get('/admin/test/submissions?dl=course&include_all=1')
        self.assertEquals(resp.content_type, 'application/x-gzip')

    def test_csv_download(self):
        '''Tests if downloading csv returns the right filetype'''
        print "\033[1m-> web-admin: course CSV download\033[0m"
        resp = appt.get('/admin/test?csv')
        self.assertEquals(resp.content_type, 'text/csv')
        resp = appt.get('/admin/test/tasks?csv')
        self.assertEquals(resp.content_type, 'text/csv')

    def tearDown(self):
        pass


class web_admin_tasks(unittest.TestCase):

    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin': True, 'username': "testadmin1", "realname": "Test", "email": "mail@test.com"})

    def test_student_list(self):
        '''Tests if student list displays correctly'''
        print "\033[1m-> web-admin: task students list\033[0m"
        resp = appt.get('/admin/test/task/task1')
        resp.mustcontain('Download all submissions')
        resp.mustcontain('CSV')

    def test_task_download(self):
        '''Tests if downloading all task submissions returns a tarfile'''
        print "\033[1m-> web-admin: task tarfile download\033[0m"
        resp = appt.get('/admin/test/submissions?dl=task&task=task1')
        self.assertEquals(resp.content_type, 'application/x-gzip')
        resp = appt.get('/admin/test/submissions?dl=task&task=task1&include_all=1')
        self.assertEquals(resp.content_type, 'application/x-gzip')

    def test_csv_download(self):
        '''Tests if downloading csv returns the right filetype'''
        print "\033[1m-> web-admin: task CSV download\033[0m"
        resp = appt.get('/admin/test/task/task1?csv')
        self.assertEquals(resp.content_type, 'text/csv')

    def tearDown(self):
        pass


class web_admin_students(unittest.TestCase):

    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin': True, 'username': "testadmin1", "realname": "Test", "email": "mail@test.com"})

    def test_task_list(self):
        '''Tests if task list displays correctly'''
        print "\033[1m-> web-admin: course student tasks list\033[0m"
        resp = appt.get('/admin/test/student/testadmin1')
        resp.mustcontain('Download all submissions')
        resp.mustcontain('Download submissions')
        resp.mustcontain('View')
        resp.mustcontain('CSV')
        resp.mustcontain('Task 1')
        resp.mustcontain('Task 2')
        resp.mustcontain('Task 3')
        resp.mustcontain('Task 4')

    def test_student_download(self):
        '''Tests if downloading all student submissions returns a tarfile'''
        print "\033[1m-> web-admin: course student tarfile download\033[0m"
        resp = appt.get('/admin/test/submissions?dl=student&username=testadmin1', status="*")
        if resp.status_int == 404:
            resp.mustcontain("There's no submission that matches your request")
        else:
            self.assertEquals(resp.content_type, 'application/x-gzip')
        resp = appt.get('/admin/test/submissions?dl=student&username=testadmin1&include_all=1', status="*")
        if resp.status_int == 404:
            resp.mustcontain("There's no submission that matches your request")
        else:
            self.assertEquals(resp.content_type, 'application/x-gzip')

    def test_csv_download(self):
        '''Tests if downloading csv returns the right filetype'''
        print "\033[1m-> web-admin: course student CSV download\033[0m"
        resp = appt.get('/admin/test/student/testadmin1?csv')
        self.assertEquals(resp.content_type, 'text/csv')

    def tearDown(self):
        pass


class web_admin_submissions(unittest.TestCase):

    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin': True, 'username': "testadmin1", "realname": "Test", "email": "mail@test.com"})

    def test_submissions_list(self):
        '''Tests if the submissions list displays correctly'''
        print "\033[1m-> web-admin: student task submissions list\033[0m"
        resp = appt.get('/admin/test/student/testadmin/task1')
        resp.mustcontain('Download all submissions')
        resp.mustcontain('CSV')

    def test_submissions_download(self):
        '''Tests if downloading all submissions returns a tarfile'''
        print "\033[1m-> web-admin: submissions tarfile download\033[0m"
        resp = appt.get('/admin/test/submissions?dl=student_task&username=testadmin1&task=task1', status="*")
        if resp.status_int == 404:
            resp.mustcontain("There's no submission that matches your request")
        else:
            self.assertEquals(resp.content_type, 'application/x-gzip')
        resp = appt.get('/admin/test/submissions?dl=student_task&username=testadmin1&task=task1&include_all=1', status="*")
        if resp.status_int == 404:
            resp.mustcontain("There's no submission that matches your request")
        else:
            self.assertEquals(resp.content_type, 'application/x-gzip')

    def test_csv_download(self):
        '''Tests if downloading csv returns the right filetype'''
        print "\033[1m-> web-admin: submissions CSV download\033[0m"
        resp = appt.get('/admin/test/student/testadmin1/task1?csv')
        self.assertEquals(resp.content_type, 'text/csv')

    def tearDown(self):
        pass


if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests', {}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> web-admin: tests cannot be run remotely\033[0m"
