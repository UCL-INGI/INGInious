import unittest
import shutil

if __name__ == "__main__":
    testmodules = [
        'tests.common_courses',
        'tests.common_tasks',
        'tests.backend_jobs',
        'tests.web_login',
        'tests.web_courses',
        'tests.web_tasks',
        'tests.web_submissions',
        'tests.web_admin'
        ]

    suite = unittest.TestSuite()

    for t in testmodules:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

    unittest.TextTestRunner().run(suite)
    
    shutil.rmtree('./tests/sessions')
