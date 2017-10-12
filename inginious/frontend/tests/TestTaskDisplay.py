# -*- coding: utf-8 -*-



from inginious.frontend.tests.TestLogin import LoggedInTest, RegisteredTest


class TestDisplaySuperAdmin(LoggedInTest):
    login = "test"
    password = "test"

    def test_register(self):
        driver = self.driver

        driver.get(self.base_url + "/course/test/helloworld")
        self.assertEqual("Hello World!", driver.find_element_by_css_selector("h2").text)
        self.assertEqual("print 'Hello World!'", driver.find_element_by_xpath("//div[@id='content']/pre").text)
        self.assertEqual("Not yet attempted", driver.find_element_by_id("task_status").text)
        self.assertEqual("0.0", driver.find_element_by_id("task_grade").text)
        self.assertEqual("0", driver.find_element_by_id("task_tries").text)
        self.assertEqual("Submit", driver.find_element_by_id("task-submit").text)


class TestDisplayAdmin(TestDisplaySuperAdmin):
    login = "test2"
    password = "test"


class TestDisplayUserAfterDeadline(RegisteredTest):
    login = "test3"
    password = "test"
    course = "test"

    def test_register(self):
        driver = self.driver

        driver.get(self.base_url + "/course/test/helloworld")
        self.assertEqual("Hello World!", driver.find_element_by_css_selector("h2").text)
        self.assertEqual("print 'Hello World!'", driver.find_element_by_xpath("//div[@id='content']/pre").text)
        self.assertEqual("Not yet attempted", driver.find_element_by_id("task_status").text)
        self.assertEqual("0.0", driver.find_element_by_id("task_grade").text)
        self.assertEqual("0", driver.find_element_by_id("task_tries").text)
        try:
            driver.implicitly_wait(2)
            driver.find_element_by_id("task-submit")
            assert False and "The user can still submit, but the deadline is reached"
        except:
            pass
