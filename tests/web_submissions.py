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
class web_submissions(unittest.TestCase):
    def setUp(self):
        inginious.frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})

    def test_code(self):
        ''' Tests submission and check of a code '''
        print "\033[1m-> web-submissions: code-problem submission\033[0m"
        resp = appt.post('/course/test/task1', {"@action":"submit", "unittest/decimal": "2"})
        js = json.loads(resp.body)
        assert "status" in js and "submissionid" in js and js["status"] == "ok"
        sub_id = js["submissionid"]
        
        for tries in range(0, 100):
            time.sleep(1)
            resp = appt.post('/course/test/task1', {"@action":"check", "submissionid":sub_id})
            js = json.loads(resp.body)
            assert "status" in js and "status" != "error"
            if js["status"] == "done":
                assert "result" in js and js["result"] != "error"
                break
    
    def test_match(self):
        ''' Tests submission and check of a code '''
        print "\033[1m-> web-submissions: match-problem submission\033[0m"
        resp = appt.post('/course/test2/task1', {"@action":"submit", "unittest": "Answer 1"})
        js = json.loads(resp.body)
        assert "status" in js and "submissionid" in js and js["status"] == "ok"
        sub_id = js["submissionid"]
        
        for tries in range(0, 100):
            time.sleep(1)
            resp = appt.post('/course/test2/task1', {"@action":"check", "submissionid":sub_id})
            js = json.loads(resp.body)
            assert "status" in js
            if js["status"] == "done":
                assert "result" in js and js["result"] == "success"
                break
    
    def test_correct_multichoice(self):
        ''' Tests correct submission and check of a multichoice '''
        print "\033[1m-> web-submissions: correct multi-choice problem submission\033[0m"
        resp = appt.post('/course/test2/task3', {"@action":"submit", "unittest": ["1","0"]})
        js = json.loads(resp.body)
        assert "status" in js and "submissionid" in js and js["status"] == "ok"
        sub_id = js["submissionid"]
        
        for tries in range(0, 100):
            time.sleep(1)
            resp = appt.post('/course/test2/task3', {"@action":"check", "submissionid":sub_id})
            js = json.loads(resp.body)
            assert "status" in js
            if js["status"] == "done":
                assert "result" in js and js["result"] == "success"
                break

    def test_incorrect_multichoice(self):
        ''' Tests incorrect submission and check of a multichoice '''
        print "\033[1m-> web-submissions: incorrect multi-choice problem submission\033[0m"
        resp = appt.post('/course/test2/task3', {"@action":"submit", "unittest": ["1"]})
        js = json.loads(resp.body)
        assert "status" in js and "submissionid" in js and js["status"] == "ok"
        sub_id = js["submissionid"]
        
        for tries in range(0, 100):
            time.sleep(1)
            resp = appt.post('/course/test2/task3', {"@action":"check", "submissionid":sub_id})
            js = json.loads(resp.body)
            assert "status" in js
            if js["status"] == "done":
                assert "result" in js and js["result"] == "failed"
                break
    
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not inginious.common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> web-submissions: tests cannot be run remotely\033[0m"
