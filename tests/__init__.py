import unittest
import webtest
import app_frontend
import common.base
import frontend
import frontend.session
import common.base
import os

if not os.path.basename(os.getcwd()) == 'doc':
    app = app_frontend.get_app(os.path.dirname(os.path.realpath(__file__)) + "/configuration.json")
    appt = webtest.TestApp(common.base.INGIniousConfiguration.get('tests', {}).get('host_url', app.wsgifunc()))
