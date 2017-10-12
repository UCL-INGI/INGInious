# -*- coding: utf-8 -*-
import time

from selenium.webdriver.common.by import By

from inginious.frontend.tests.TestLogin import LoggedInTest


class TestTaskSubmission(LoggedInTest):
    login = "test"
    password = "test"

    def test_submit(self):
        driver = self.driver

        driver.get(self.base_url + "/course/test/helloworld")
        print("-----------------Trying to find textarea-----------------")
        for i in range(5):
            try:
                if self.is_element_present(By.CSS_SELECTOR, "div.CodeMirror textarea"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        print("-----------------Calling script-----------------")
        driver.execute_script("""codeEditors[0].setValue('print "Hello World!"')""")
        time.sleep(2)
        self.assertEqual("""print "Hello World!\"""", driver.find_element_by_css_selector('textarea.code-editor').get_attribute('value'))
        print("-----------------Clicking-----------------")
        driver.find_element_by_id("task-submit").click()
        print("-----------------Trying to find task alert-----------------")
        for i in range(5):
            try:
                if self.is_element_present(By.XPATH, "//div[@id='task_alert']/div/p"):
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.fail("time out")
        print("-----------------Done-----------------")
        print(driver.find_element_by_xpath("//div[@id='task_alert']/div").text)
        self.assertEqual("You solved this difficult task!", driver.find_element_by_xpath("//div[@id='task_alert']/div/p").text)
        self.assertEqual("100.0", driver.find_element_by_id("task_grade").text)
        self.assertEqual("Succeeded", driver.find_element_by_id("task_status").text)
        self.assertEqual("1", driver.find_element_by_id("task_tries").text)
