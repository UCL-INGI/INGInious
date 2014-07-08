from nose.tools import *
from paste.fixture import TestApp
import frontend.session
import app_frontend
import json
import time

class testIndex:
    def testDisplay(self):
        middleware = []
        testApp = TestApp(app_frontend.app.wsgifunc(*middleware))
        r = testApp.get('/')
        r.mustcontain('Unit test course name')

class testCourse:
    def testDisplay(self):
        middleware = []
        testApp = TestApp(app_frontend.app.wsgifunc(*middleware))
        r = testApp.get('/course/test')
        r.mustcontain('Unit test course name')
        r.mustcontain('Unit test decimal question')
        r.mustcontain('Unit test int question')
        r.mustcontain('Unit test multiple question')
        r.mustcontain('Unit test question')

class testTask:
    def testDisplayWorking(self):
        """ Checks if the page for the "working" task is... working """
        middleware = []
        testApp = TestApp(app_frontend.app.wsgifunc(*middleware))
        r = testApp.get('/course/test/workingcode')
        r.mustcontain("Unit test question")
        r.mustcontain("unit_test_exercice")
    def testCheckWorking(self, inputVal="ok"):
        middleware = []
        testApp = TestApp(app_frontend.app.wsgifunc(*middleware))
        r = testApp.post('/course/test/workingcode', {"@action":"submit", "unit_test_exercice":inputVal})
        j = json.loads(r.body)
        assert "status" in j and "submissionId" in j and j["status"] == "ok"
        return j
    def testCheckWorking2(self):
        middleware = []
        j = self.testCheckWorking()
        testApp = TestApp(app_frontend.app.wsgifunc(*middleware))
        for tries in range(0, 100):
            time.sleep(1)
            r = testApp.post('/course/test/workingcode', {"@action":"check", "submissionId":j["submissionId"]})
            j = json.loads(r.body)
            assert "status" in j and "status" != "error"
            if j["status"] == "done":
                assert "result" in j and j["result"] != "error"
        assert False
    def testCheckWorking3(self):
        middleware = []
        testApp = TestApp(app_frontend.app.wsgifunc(*middleware))
        r = testApp.post('/course/test/workingcode', {"@action":"submit", "unit_test_exercice":""})
        j = json.loads(r.body)
        assert "status" in j and j["status"] == "error"  # no input...
        return j
