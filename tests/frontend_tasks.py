import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base
import json
import time
from tests import *

class frontend_tasks_display(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> frontend_tasks_display:setUp\033[0m"
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
        
    def test_basic_tasks_list(self):
        '''Tests if a basic course list is correct'''
        resp = appt.get('/course/test')
        self.assertEqual(resp.status_int,200)
        resp.mustcontain('Task 1')
        resp.mustcontain('Task 2')
        resp.mustcontain('Task 3')
        resp.mustcontain('Task 4')
    
    def test_decimal_rendering(self):
        '''Tests rendering of a decimal question '''
        resp = appt.get('/course/test/task1')
        resp.mustcontain('Header 1')
        resp.mustcontain('input type="number" name="unittest/decimal')
        resp.mustcontain('Here should go some introductory text.')
    
    def test_integer_rendering(self):
        '''Tests rendering of a decimal question '''
        resp = appt.get('/course/test/task2')
        resp.mustcontain('Question 2')
        resp.mustcontain('Header 2')
        resp.mustcontain('input type="number" name="unittest/int')
        resp.mustcontain('Here should go some introductory text.')
    
    def test_multichoice_rendering(self):
        '''Tests rendering of a multichoice question '''
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
        resp = appt.get('/course/test/task4')
        resp.mustcontain('Question 4')
        resp.mustcontain('Header 4')
        resp.mustcontain('div id="unittest" class="aceEditor"')
    
    def test_accessibility(self):
        '''Tests accessibility of different tasks '''
        resp = appt.get('/course/test2')
        resp.mustcontain('Task 1')
        resp.mustcontain('Task 3') # 1970 - 2033
        resp.mustcontain('Task 2 (task currently unavailable)') # Accesibility 1970-1970
    
    def tearDown(self):
        print "\033[1m-> frontend_tasks_display:tearDown\033[0m"

class frontend_tasks_submit(unittest.TestCase):
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
