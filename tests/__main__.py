import unittest
import shutil

if __name__ == "__main__":
    testmodules = [
        'tests.frontend_login',
        'tests.frontend_courses',
        'tests.frontend_tasks',
        'tests.frontend_submissions',
        'tests.frontend_admin',
        ]

    suite = unittest.TestSuite()

    for t in testmodules:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

    unittest.TextTestRunner().run(suite)
    
    shutil.rmtree('./tests/sessions')
