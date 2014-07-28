import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base
import json
import time
from tests import *

class frontend_submissions(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> frontend_tasks_submit:setUp\033[0m"
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})

    def test_code(self):
        ''' Tests submission and check of a code '''
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
        print "\033[1m-> frontend_tasks_submit:tearDown\033[0m"

if __name__ == "__main__":
    unittest.main()
