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

os.environ['INGInious_PATH_WEBAPP'] = '/var/www/INGInious'
os.environ['INGInious_CONFIG_WEBAPP'] = '/var/www/INGInious/configuration.yaml'

if os.getenv('INGInious_PATH_WEBAPP'):
    sys.path.append(os.getenv('INGInious_PATH_WEBAPP'))
    os.chdir(os.getenv('INGInious_PATH_WEBAPP'))
else:
    print 'INGInious_PATH_WEBAPP NOT FOUND'

import signal
import logging

from inginious.common.base import load_json_or_yaml
from inginious.common.log import init_logging, CustomLogMiddleware
import inginious.frontend.webapp.app
from inginious.frontend.webapp.installer import Installer

import web

if os.getenv('INGInious_CONFIG_WEBAPP'):
    configFile = os.getenv('INGInious_CONFIG_WEBAPP')
elif os.path.isfile("./configuration.yaml"):
    configFile = "./configuration.yaml"
elif os.path.isfile("./configuration.json"):
    configFile = "./configuration.json"
else:
    raise Exception("No configuration file found")

config=load_json_or_yaml(configFile)
init_logging(config.get('log_level', 'INFO'))
app, close_app_func = inginious.frontend.webapp.app.get_app(hostname=None,
                                                            port=None,
                                                            sshhost=None,
                                                            sshport=8001,
                                                            config=config)
func = app.wsgifunc()
func = CustomLogMiddleware(func, logging.getLogger("inginious.webapp.requests"))

application = func
