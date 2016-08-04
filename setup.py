#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import sys

import os
from setuptools import setup, find_packages

import inginious

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

install_requires = [
    "docker-py>=1.9.0",
    "docutils>=0.12",
    "pymongo>=3.2.2",
    "PyYAML>=3.11",
    "web.py>=0.40.dev0",
    "pylti>=0.4.1",
    "watchdog >= 0.8.3",
    "msgpack-python >= 0.4.7",
    "pyzmq >= 15.3.0"
]
test_requires = [
    "selenium",
    "nose",
    "pyvirtualdisplay"
]

# Platform specific dependencies
if not on_rtd:
    install_requires += ["pytidylib>=0.2.4", "sphinx-rtd-theme>=0.1.8"]
else:
    install_requires += test_requires + ["Pygments>=2.0.2"]

if sys.platform == 'win32':
    install_requires += ["pbs>=0.110"]
else:
    install_requires += ["sh>=1.11"]

# Setup
setup(
    name="INGInious",
    version=inginious.__version__,
    description="An intelligent grader that allows secured and automated testing of code made by students.",
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=test_requires,
    extras_require={
        "cgi": ["flup>=1.0.3.dev"],
        "ldap": ["simpleldap>=0.9"],
        "test": test_requires
    },

    scripts=[
        'inginious-agent-docker',
        'inginious-agent-mcq',
        'inginious-backend',
        'inginious-lti',
        'inginious-webapp',
        'inginious-install',
        'inginious/utils/check_task_description/inginious-check-task',
        'inginious/utils/sync/inginious-synchronize',
        'inginious/utils/task_auto_tester/inginious-auto-test-task',
        'inginious/utils/task_converter/inginious-old-task-converter',
        'inginious/utils/task_manual_tester/inginious-test-task',
        'inginious/utils/remote_debugger/inginious-remote-debug',
        'inginious/utils/container_update/inginious-container-update'
    ],

    include_package_data=True,

    test_suite='nose.collector',

    author="INGInious contributors",
    author_email="inginious@info.ucl.ac.be",
    license="AGPL 3",
    url="https://github.com/UCL-INGI/INGInious",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
)
