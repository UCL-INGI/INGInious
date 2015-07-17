# -*- coding: utf-8 -*-
from selenium.selenium import selenium
import unittest, time, re

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("192.168.59.103", 4444, "*googlechrome", "http://192.168.59.3:8081/index?logoff")
        self.selenium.start()
    
    def test_login(self):
        sel = self.selenium
        sel.open("/index?logoff")
        sel.type("name=login", "test")
        sel.type("name=password", "test")
        sel.click("//button[@type='submit']")
        self.assertEqual("Logged in as test", sel.get_text("css=p.navbar-text"))
        sel.click("css=i.fa.fa-sign-out")
        sel.wait_for_page_to_load("30000")
        self.assertEqual("Hello! Welcome on the INGInious platform.", sel.get_text("css=h2"))
        self.assertEqual("Log in", sel.get_text("//button[@type='submit']"))
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
