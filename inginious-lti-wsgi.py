#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#

""" Starts the webapp """

import sys
import os

# See https://gist.github.com/GrahamDumpleton/b380652b768e81a7f60c
# for alternate solutions

os.environ['INGInious_PATH_LTI'] = '/var/www/INGInious'
os.environ['INGInious_CONFIG_LTI'] = '/var/www/INGInious/configuration.lti.yaml'

if os.getenv('INGInious_PATH_LTI'):
    sys.path.append(os.getenv('INGInious_PATH_LTI'))
    os.chdir(os.getenv('INGInious_PATH_LTI'))

import signal
import logging

from inginious.common.base import load_json_or_yaml

from inginious.frontend.common.static_middleware import StaticMiddleware
from inginious.common.log import init_logging, CustomLogMiddleware

import inginious.frontend.lti.app
from inginious.frontend.webapp.installer import Installer

import web

if os.getenv('INGInious_CONFIG_LTI'):
    configFile = os.getenv('INGInious_CONFIG_LTI')
elif os.path.isfile("./configuration.lti.yaml"):
    configFile = "./configuration.lti.yaml"
elif os.path.isfile("./configuration.lti.json"):
    configFile = "./configuration.lti.json"
else:
    raise Exception("No configuration file found")

config=load_json_or_yaml(configFile)
app, close_app_func = inginious.frontend.lti.app.get_app(config=config)
func = app.wsgifunc()
func = CustomLogMiddleware(func, logging.getLogger("inginious.webapp.requests"))
application = func
