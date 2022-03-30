#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import sys
import os
from setuptools import setup, find_packages

install_requires = [
    "docker>=2.5.0",
    "docutils>=0.14",
    "pymongo>=3.2.2",
    "PyYAML>=3.11",
    "Jinja2 >= 2.10",
    "lti>=0.9.0",
    "oauth2>=1.9.0.post1",
    "httplib2>=0.9",
    "watchdog >= 0.8.3",
    "msgpack >= 1.0.0",
    "pyzmq >= 15.3.0",
    "natsort >= 5.0.1",
    "psutil >= 4.4.2",
    "zipstream >= 1.1.4",
    "WsgiDAV >= 3.0.0",
    "Werkzeug >= 1.0.0",
    "itsdangerous >= 1.1.0",
    "Flask >= 1.1.0",
    "Flask-Mail >= 0.9.1",
    "importlib_metadata >= 3.7.0",
    'dataclasses >= 0.8; python_version < "3.7.0"',
    "pytidylib>=0.2.4",
    "sphinx-autodoc-typehints>=1.12.0",
]

test_requires = [
    "selenium == 3.141.0",
    "nose",
    "pyvirtualdisplay"
]

doc_requires = [
    "sphinx==4.5.0",
    "sphinx_rtd_theme==1.0.0",
    "sphinx-tabs==3.3.1",
    "ipython==8.2.0"
]

if sys.platform == 'win32':
    install_requires += ["pbs>=0.110"]
else:
    install_requires += ["sh>=1.11"]

# Setup
setup(
    name="INGInious",
    use_scm_version=True,
    description="An intelligent grader that allows secured and automated testing of code made by students.",
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    install_requires=install_requires,
    tests_require=test_requires,
    extras_require={
        "cgi": ["flup>=1.0.3.dev"],
        "ldap": ["ldap3"],
        "saml2": ["python3-saml"],
        "uwsgi": ["uwsgi"],
        "test": test_requires,
        "doc": test_requires + doc_requires
    },

    scripts=[
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
    ],

    include_package_data=True,
    test_suite='nose.collector',
    author="INGInious contributors",
    author_email="inginious@info.ucl.ac.be",
    license="AGPL 3",
    url="https://github.com/UCL-INGI/INGInious",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf8').read()
)
