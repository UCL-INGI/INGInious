# -*- coding: utf-8 -*-
from selenium.selenium import selenium
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
import unittest
import os
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re
from nose.plugins.skip import SkipTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TEST_ENV = os.environ.get("TEST_ENV", None)
CUSTOM_SELENIUM_EXECUTOR = os.environ.get("CUSTOM_SELENIUM_EXECUTOR", None)
CUSTOM_SELENIUM_BASE_URL = os.environ.get("CUSTOM_SELENIUM_BASE_URL", None)

class SeleniumTest(unittest.TestCase):

        
    def setUp(self):
        if TEST_ENV == "boot2docker":
            self.driver = webdriver.Remote(command_executor=(CUSTOM_SELENIUM_EXECUTOR or 'http://192.168.59.103:4444/wd/hub'),
                                           desired_capabilities=DesiredCapabilities.CHROME)
            self.base_url = CUSTOM_SELENIUM_BASE_URL or "http://192.168.59.3:8081"
        elif TEST_ENV == "travis":
            raise SkipTest("Frontend tests are not yet available on a Travis environment")
        elif TEST_ENV == "local" or True:
            self.driver = webdriver.Firefox()
            self.base_url = CUSTOM_SELENIUM_BASE_URL or "http://127.0.0.1:8081"
        else:
            raise SkipTest("Env variable TEST_ENV is not properly configured. Please take a look a the documentation to properly configure your "
                           "test environment.")

        self.driver.implicitly_wait(30)
        self.verificationErrors = []
        self.accept_next_alert = True


    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e:
            return False
        return True


    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException, e:
            return False
        return True


    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True


    def wait_for_presence_css(self, selector):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)