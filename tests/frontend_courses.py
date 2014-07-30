import unittest
import webtest
import app_frontend
import common
import common.base
from pymongo import MongoClient
import frontend
import frontend.base
import frontend.session
import frontend.custom
import frontend.custom.courses
import frontend.submission_manager
from tests import *
import time

class frontend_courses(unittest.TestCase):
    def setUp(self):
        # Droping database
        client = frontend.base.get_database().connection
        client.drop_database(common.base.INGIniousConfiguration.get('mongo_opt', {}).get('database', 'INGIniousTest'))
        #Init test session
        frontend.session.init(app, {'loggedin':True, 'username':"test", "realname":"Test", "email":"mail@test.com"})
    
    def test_completion_percentage(self):
        '''Tests completion percentage of a course'''
        print "\033[1m-> frontend-course: completion percentage\033[0m"
        c = frontend.custom.courses.FrontendCourse('test2')
        number = len(c.get_tasks())
        t = common.tasks.Task(c, 'task1')
        
        #Launch a task
        sid = frontend.submission_manager.add_job(t, {"unittest":"Answer 1"})
        while not frontend.submission_manager.is_done(sid):
            time.sleep(1)
        
        #Assert completion percentage is 100/number percent
        assert int(c.get_user_completion_percentage()) == int(100/number)
    
    def test_last_submissions(self):
        '''Tests lasts submissions '''
        print "\033[1m-> frontend-course: lasts submissions\033[0m"
        c = frontend.custom.courses.FrontendCourse('test2')
        number = len(c.get_tasks())
        t = common.tasks.Task(c, 'task1')
        
        #Launch a task
        sid = frontend.submission_manager.add_job(t, {"unittest":"Answer 1"})
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
    unittest.main()
