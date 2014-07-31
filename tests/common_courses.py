import unittest
import common.base
import common.courses
from tests import *

class common_courses(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_course_loading(self):
        '''Tests if a course file loads correctly'''
        print "\033[1m-> common-courses: course loading\033[0m"
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
        print "\033[1m-> common-courses: all courses loading\033[0m"
        c = common.courses.Course.get_all_courses()
        assert 'test' in c
        assert 'test2' in c
        assert 'test3' in c
    
    def test_tasks_loading(self):
        '''Tests loading tasks from the get_tasks method'''
        print "\033[1m-> common-courses: course tasks loading\033[0m"
        c = common.courses.Course('test')
        t = c.get_tasks()
        assert 'task1' in t
        assert 'task2' in t
        assert 'task3' in t
        assert 'task4' in t
        
    def tearDown(self):
        pass

if __name__ == "__main__":
    if not common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> common-courses: tests cannot be run remotely\033[0m"
