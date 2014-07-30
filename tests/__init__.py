import unittest

import webtest

import app_frontend
import common.base
import frontend
import frontend.session
if __name__ == "__main__":
    app = app_frontend.get_app("tests/configuration.json")
    appt = webtest.TestApp(app.wsgifunc())
