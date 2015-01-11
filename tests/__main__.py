import unittest
import common
import common.base
from tests import *

if __name__ == "__main__":
    
    testmodules = ['tests.load_sync', 'tests.load_async']
    
    if not frontend.configuration.INGIniousConfiguration.get('tests',{}).get('host_url', ''):
        modules = ['tests.common_courses',
            'tests.common_tasks',
            'tests.backend_jobs',
            'tests.frontend_courses',
            'tests.frontend_tasks',
            'tests.web_login', 
            'tests.web_courses',
            'tests.web_tasks',
            'tests.web_submissions', 
            'tests.web_admin'
            ]
        modules.extend(testmodules)
        testmodules = modules
    
    suite = unittest.TestSuite()

    for t in testmodules:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

    unittest.TextTestRunner().run(suite)
