import unittest
import common.base
import common.courses
from tests import *

class common_courses(unittest.TestCase):
    def setUp(self):
        print "\033[1m-> common_courses:setUp_:begin\033[0m"
    
    def test_course_loading(self):
        '''Tests if a course file loads correctly'''
        c = common.courses.Course('test')
        assert c.get_id() == 'test'
        assert c._content['accessible'] == None
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 1'
        
        c = common.courses.Course('test2')
        assert c.get_id() == 'test2'
        assert c._content['accessible'] == '1970-01-01/2033-01-01'
        assert c._content['admins'] == ['testadmin1']
        assert c._content['name'] == 'Unit test 2'
        
        c = common.courses.Course('test3')
        assert c.get_id() == 'test3'
        assert c._content['accessible'] == '1970-01-01/1970-12-31'
        assert c._content['admins'] == ['testadmin1', 'testadmin2']
        assert c._content['name'] == 'Unit test 3'
    
    def test_all_courses_loading(self):
        '''Tests if all courses are loaded by Course.get_all_courses()'''
        c = common.courses.Course.get_all_courses()
        assert 'test' in c
        assert 'test2' in c
        assert 'test3' in c
    
    def test_tasks_loading(self):
        '''Tests loading tasks from the get_tasks method'''
        c = common.courses.Course('test')
        t = c.get_tasks()
        assert 'task1' in t
        assert 'task2' in t
        assert 'task3' in t
        assert 'task4' in t
        
    def tearDown(self):
        print "\033[1m-> common_courses:setUp_:tearDown\033[0m"

if __name__ == "__main__":
    unittest.main()
