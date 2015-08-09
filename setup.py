#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
import os

from setuptools import setup, find_packages
import sys
import inginious

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

install_requires = [
    "docker-py==1.3.0dev",
    "docutils>=0.12",
    "multiprocessing>=2.6.2.1",
    "plumbum>=1.5.0",
    "Pygments>=2.0.2",
    "pymongo>=3.0.3",
    "pytidylib>=0.2.4",
    "PyYAML>=3.11",
    "requests>=2.7.0",
    "rpyc>=3.3.0",
    "six>=1.9.0",
    "web.py>=0.37",
    "websocket-client>=0.32.0",
    "pylti>=0.3.2",
    "mock >= 1.0.1"
]

if not on_rtd:
    install_requires += [
        "simpleldap>=0.8",
        "python-ldap>=2.4.19",
    ]

if sys.platform == 'win32':
    install_requires += ["pbs>=0.110"]
else:
    install_requires += ["sh>=1.11"]

if sys.platform.startswith('linux') and not on_rtd:
    install_requires += ["cgroup-utils>=0.5"]

setup(
    name="INGInious",
    version=inginious.__version__,
    description="An intelligent grader that allows secured and automated testing of code made by students.",
    packages=find_packages(),
    dependency_links=["git+https://github.com/GuillaumeDerval/docker-py.git#egg=docker-py-1.3.0dev"],
    install_requires=install_requires,
    tests_require=[
        "selenium",
        "nose",
        "pyvirtualdisplay"
    ],
    extras_require={
        "cgi": ["flup"]
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
        'inginious/utils/task_manual_tester/inginious-test-task'
    ],

    include_package_data=True,

    test_suite='nose.collector',

    author = u"Université catholique de Louvain",
    author_email = "inginious@info.ucl.ac.be",
    license = "AGPL 3",
    url = "https://github.com/UCL-INGI/INGInious",
    long_description =open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
)
