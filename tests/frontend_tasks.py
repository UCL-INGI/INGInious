import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base
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

    def tearDown(self):
        print "\033[1m-> frontend_tasks_display:tearDown\033[0m"

if __name__ == "__main__":
    unittest.main()
