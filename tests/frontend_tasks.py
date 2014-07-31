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
import frontend.custom.tasks
import frontend.submission_manager
from tests import *
import time

class frontend_tasks(unittest.TestCase):
    def setUp(self):
        # Droping database
        client = frontend.base.get_database().connection
        client.drop_database(common.base.INGIniousConfiguration.get('mongo_opt', {}).get('database', 'INGIniousTest'))
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
    if not common.base.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        unittest.main()
    else:
        print "\033[31;1m-> frontend-tasks: tests cannot be run remotely\033[0m"
