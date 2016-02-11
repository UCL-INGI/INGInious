#!/usr/bin/env python
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
    "docker-py==1.3.0.dev0",
    "docutils>=0.12",
    "plumbum>=1.5.0",
    "pymongo>=3.0.3",
    "PyYAML>=3.11",
    "requests>=2.7.0",
    "rpyc>=3.3.0",
    "six>=1.9.0",
    "web.py-INGI>=0.38dev1",
    "websocket-client>=0.32.0",
    "pylti>=0.3.2",
    "mock >= 1.0.1",
    "watchdog >= 0.8.3"
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

if sys.platform.startswith('linux') and not on_rtd:
    install_requires += ["cgroup-utils>=0.5"]

# Setup
setup(
    name="INGInious",
    version=inginious.__version__,
    description="An intelligent grader that allows secured and automated testing of code made by students.",
    packages=find_packages(),
    dependency_links=["git+https://github.com/GuillaumeDerval/docker-py.git#egg=docker-py-1.3.0.dev0"],
    install_requires=install_requires,
    tests_require=test_requires,
    extras_require={
        "cgi": ["flup"],
        "ldap": ["simpleldap>=0.8", "python-ldap>=2.4.19"],
        "test": test_requires
    },

    scripts=[
        'inginious-agent',
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

    author=u"INGInious contributors",
    author_email="inginious@info.ucl.ac.be",
    license="AGPL 3",
    url="https://github.com/UCL-INGI/INGInious",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
)
