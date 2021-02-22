# -*- coding: utf-8 -*-

import os
import threading
import unittest

from werkzeug.serving import make_server
from inginious.frontend.app import get_app
from nose.plugins.skip import SkipTest
from pymongo import MongoClient
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from werkzeug.middleware.shared_data import SharedDataMiddleware

TEST_ENV = os.environ.get("TEST_ENV", None)
CUSTOM_SELENIUM_EXECUTOR = os.environ.get("CUSTOM_SELENIUM_EXECUTOR", None)
CUSTOM_SELENIUM_BASE_URL = os.environ.get("CUSTOM_SELENIUM_BASE_URL", None)
CUSTOM_FRONTEND_CONF_FILE = os.environ.get("CUSTOM_FRONTEND_CONF_FILE", None)


def _start_frontend(config, host, port, ssh_port):
    semaphore = threading.Semaphore(0)

    def active_callback():
        semaphore.release()

    func, close_app_func = get_app(config)

    inginious_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    func = SharedDataMiddleware(func, [
        ('/static/', os.path.join(inginious_root_path, 'frontend', 'static'))
    ])
    server = make_server(host, port, func)

    class FrontendThread(threading.Thread):
        def __init__(self):
            super(FrontendThread, self).__init__()
            self.daemon = True

        def run(self):
            try:
                server.start()
            except:
                server.stop()

    thread = FrontendThread()
    thread.start()
    semaphore.acquire()
    return thread, server, close_app_func


def _drop_database(config):
    """ Drop the database before running any test """
    mongo_client = MongoClient(host=config.get('host', 'localhost'))
    mongo_client.drop_database(config.get('database', 'INGIniousFrontendTest'))


class SeleniumTest(unittest.TestCase):
    def setUp(self):
        self.frontend_config = {
            "backend": "remote",
            "docker_daemons": [{
                "remote_host": "192.168.59.103",
                "remote_docker_port": 2375,
                "remote_agent_port": 63456
            }],
            "mongo_opt": {"host": "localhost", "database": "INGIniousFrontendTest"},
            "tasks_directory": "./inginious/tasks",
            "containers": {
                "default": "ingi/inginious-c-default",
                "sekexe": "ingi/inginious-c-sekexe",
            },
            "superadmins": ["test"],
            "plugins": [
                {
                    "plugin_module": "inginious.frontend.plugins.auth.demo_auth",
                    "users": {"test": "test", "test2": "test", "test3": "test"}
                }
            ]
        }

        if TEST_ENV == "boot2docker":
            self.display = None
            self.driver = webdriver.Remote(command_executor=(CUSTOM_SELENIUM_EXECUTOR or 'http://192.168.59.103:4444/wd/hub'),
                                           desired_capabilities=DesiredCapabilities.FIREFOX)
            self.base_url = CUSTOM_SELENIUM_BASE_URL or "http://192.168.59.3:8081"
            self.frontend_host = "192.168.59.3"
            self.frontend_port = 8081
            self.frontend_ssh_port = 8082
        elif TEST_ENV == "boot2docker-local":
            self.display = None
            self.driver = webdriver.Firefox()
            self.base_url = CUSTOM_SELENIUM_BASE_URL or "http://127.0.0.1:8081"
            self.frontend_host = "127.0.0.1"
            self.frontend_port = 8081
            self.frontend_ssh_port = 8082
        elif False and TEST_ENV == "jenkins":
            self.display = Display(visible=0, size=(1920, 1080))
            self.display.start()
            self.driver = webdriver.Firefox()
            self.base_url = CUSTOM_SELENIUM_BASE_URL or "http://localhost:8081"
            self.frontend_host = "localhost"
            self.frontend_port = 8081
            self.frontend_ssh_port = 8082
            self.frontend_config["backend"] = "local"
        else:
            raise SkipTest("Env variable TEST_ENV is not properly configured. Please take a look a the documentation to properly configure your "
                           "test environment.")

        self.driver.maximize_window()
        self.driver.implicitly_wait(30)
        self.verificationErrors = []
        self.accept_next_alert = True
        _drop_database(self.frontend_config["mongo_opt"])
        self.frontend_thread, self.frontend_server, self.close_app_func = _start_frontend(self.frontend_config,
                                                                                          self.frontend_host,
                                                                                          self.frontend_port,
                                                                                          self.frontend_ssh_port)

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException as e:
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
        if self.display is not None:
            self.display.stop()
        self.frontend_server.stop()
        self.close_app_func()
        self.frontend_thread.join()
        _drop_database(self.frontend_config["mongo_opt"])
        self.assertEqual([], self.verificationErrors)
