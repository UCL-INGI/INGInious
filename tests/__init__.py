import unittest
import webtest
import app_frontend
import frontend
import frontend.session
import common.base

app = app_frontend.get_app("tests/configuration.json")
appt = webtest.TestApp(app.wsgifunc())
