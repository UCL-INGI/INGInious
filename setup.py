#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import sys
import os
from setuptools import setup, find_packages

install_requires = [
    "docker == 6.1.3",
    "requests == 2.28.2",  # TODO: remove when https://github.com/docker/docker-py/issues/3113 is closed.
    "docutils == 0.20.1",
    "pymongo == 4.5.0",
    "PyYAML == 6.0.1",
    "Jinja2 == 3.1.2",
    "lti == 0.9.5",
    "oauth2 == 1.9.0.post1",
    "httplib2 == 0.22.0",
    "watchdog == 3.0.0",
    "msgpack == 1.0.5",
    "pyzmq == 25.1.1",
    "natsort == 8.4.0",
    "psutil == 5.9.5",
    "zipstream == 1.1.4",
    "WsgiDAV == 4.2.0",
    "Werkzeug == 2.3.7",
    "itsdangerous== 1.1.0",
    "Flask == 2.3.3",
    "Flask-Mail == 0.9.1",
    "importlib_metadata == 6.8.0",
    'dataclasses >= 0.8; python_version < "3.7.0"',
    "pytidylib == 0.3.2",
    "sphinx-autodoc-typehints == 1.24.0",
]

test_requires = [
    "pytest",
    "coverage"
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
        "cgi": ["flup>=1.0.3.dev"],
        "ldap": ["ldap3"],
        "saml2": ["python3-saml"],
        "uwsgi": ["uwsgi"],
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
