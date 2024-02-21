#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import sys
import os
from setuptools import setup, find_packages

install_requires = [
    "docker==7.0.0",
    "docutils==0.20.1",
    "Flask==3.0.2",
    "Flask-Mail==0.9.1",
    "itsdangerous==2.1.2",
    "Jinja2==3.1.3",
    "lti==0.9.5",
    "msgpack==1.0.7",
    "natsort==8.4.0",
    "psutil==5.9.8",
    "pymongo==4.6.1",
    "pytidylib==0.3.2",
    "PyYAML==6.0.1",
    "pyzmq==25.1.2",
    "requests-oauthlib==1.3.1",
    "sh==2.0.6",
    "watchdog==4.0.0",
    "Werkzeug==3.0.1",
    "MarkupSafe==2.1.5",
    "WsgiDAV==4.3.0",
    "zipstream==1.1.4",
    "argon2-cffi == 23.1.0"
]

test_requires = [
    "pytest==8.0.0",
    "coverage==7.4.1"
]

doc_requires = [
    "ipython==8.12.3",
    "sphinx==7.1.2",
    "sphinx-autodoc-typehints==2.0.0",
    "sphinx-rtd-theme==2.0.0",
    "sphinx-tabs==3.4.5"
]

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
    name="INGInious",
    use_scm_version=True,
    description="An intelligent grader that allows secured and automated testing of code made by students.",
    packages=find_packages(),
    setup_requires=['setuptools_scm'],
    install_requires=install_requires,
    tests_require=test_requires,
    extras_require={
        "cgi": ["flup==1.0.3"],
        "ldap": ["ldap3==2.9.1"],
        "saml2": ["python3-saml==1.16.0"],
        "uwsgi": ["uwsgi==2.0.24"],
        "test": test_requires,
        "doc": test_requires + doc_requires
    },
    scripts=scripts,
    include_package_data=True,
    test_suite='nose.collector',
    author="INGInious contributors",
    author_email="inginious@info.ucl.ac.be",
    license="AGPL 3",
    url="https://github.com/UCL-INGI/INGInious",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf8').read()
)
