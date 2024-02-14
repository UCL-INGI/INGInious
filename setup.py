#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import sys
import os
from setuptools import setup, find_packages


scripts = [] if os.environ.get("INGINIOUS_COMPOSE") else [
    'inginious-agent-docker',
    'inginious-agent-mcq',
    'inginious-backend',
    'inginious-webapp',
    'inginious-webdav',
    'inginious-install',
    'inginious-autotest',
    'utils/sync/inginious-synchronize',
    'utils/container_update/inginious-container-update',
    'utils/database_updater/inginious-database-update'
]

# Setup
setup(
    scripts=scripts,
    test_suite='nose.collector',
)
