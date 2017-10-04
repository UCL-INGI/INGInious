# -*- coding: utf-8 -*-
from selenium.webdriver.support.ui import Select

from inginious.frontend.tests.SeleniumTest import SeleniumTest


class TestLogin(SeleniumTest):
    def test_login(self):
        driver = self.driver
        driver.get(self.base_url + "/index?logoff")

        self.assertEqual("Hello! Welcome on the INGInious platform.", driver.find_element_by_css_selector("h2").text)

        driver.find_element_by_name("login").clear()
        driver.find_element_by_name("login").send_keys("test")
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys("test")

        driver.find_element_by_xpath("//button[@type='submit']").click()

        self.wait_for_presence_css(".navbar p.navbar-text")
        # self.assertEqual("Logged in as test", driver.find_element_by_xpath('//*[@id="wrapper"]/div[1]/div/div[2]/div/ul/li[1]/p').text)
        self.assertEqual("Log off", driver.find_element_by_id("logoff_button").text)


class LoggedInTest(SeleniumTest):
    login = "test"
    password = "test"

    def setUp(self):
        super(LoggedInTest, self).setUp()
        driver = self.driver
        driver.get(self.base_url + "/index?logoff")
        driver.find_element_by_name("login").clear()
        driver.find_element_by_name("login").send_keys(self.login)
        driver.find_element_by_name("password").clear()
        driver.find_element_by_name("password").send_keys(self.password)
        driver.find_element_by_xpath("//button[@type='submit']").click()
        self.wait_for_presence_css(".navbar p.navbar-text")


class TestRegistration(LoggedInTest):
    login = "test3"
    password = "test"

    def test_unregister(self):
        driver = self.driver
        driver.get(self.base_url + "/course/test")

        self.test_register()
        self.assertEqual("[LTEST0000] Test tasks : H2G2 - List of exercises", driver.find_element_by_css_selector("h2").text)
        driver.find_element_by_partial_link_text("Unregister from this course").click()
        self.assertEqual("[LTEST0000] Test tasks : H2G2", driver.find_element_by_css_selector("#register_courseid option[value=\"test\"]").text)

    def test_register(self):
        driver = self.driver

        driver.get(self.base_url + "/course/test")
        self.assertEqual("Error 403 You are not registered to this course.", driver.find_element_by_css_selector(".alert.alert-warning").text)
        driver.get(self.base_url + "/index")
        Select(driver.find_element_by_id("register_courseid")).select_by_visible_text("[LTEST0000] Test tasks : H2G2")
        self.assertEqual("[LTEST0000] Test tasks : H2G2", driver.find_element_by_css_selector("#register_courseid option[value=\"test\"]").text)
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.get(self.base_url + "/course/test")
        self.assertEqual("[LTEST0000] Test tasks : H2G2 - List of exercises", driver.find_element_by_css_selector("h2").text)


class RegisteredTest(LoggedInTest):
    course = "test"

    def setUp(self):
        super(RegisteredTest, self).setUp()
        driver = self.driver
        driver.get(self.base_url + "/index")
        Select(driver.find_element_by_id("register_courseid")).select_by_visible_text("[LTEST0000] Test tasks : H2G2")
        driver.find_element_by_xpath("//button[@type='submit']").click()
