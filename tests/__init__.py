import unittest
import webtest
import app_frontend
import common.base
import frontend
import frontend.session
import common.base


if __name__ == "__main__":
    app = app_frontend.get_app("tests/configuration.json")
    print common.base.INGIniousConfiguration.get('tests', {}).get('host_url', app.wsgifunc())
    appt = webtest.TestApp(common.base.INGIniousConfiguration.get('tests', {}).get('host_url', app.wsgifunc()))

