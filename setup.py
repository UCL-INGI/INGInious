#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import sys
import os
from setuptools import setup, find_packages

install_requires = [
    "docker == 7.1.0", # docker 6.1.0 ? -> docker-py = ancienne version de docker
    "docutils == 0.20.1",
    "pymongo == 4.10.1",
    "PyYAML == 6.0.2",
    "Jinja2 == 3.1.4",
    "lti == 0.9.5",
    "oauth2 == 1.9.0.post1",
    "httplib2 == 0.22.0",
    "watchdog == 4.0.2",
    "msgpack == 1.1.0",
    "pyzmq == 26.2.0",
    "natsort == 8.4.0",
    "psutil == 6.1.0",
    "zipstream == 1.1.4",
    "WsgiDAV == 4.3.3",
    "Werkzeug == 2.3.7",
    "itsdangerous == 2.2.0",
    "Flask == 2.3.3",
    "Flask-Mail == 0.10.0",
    "importlib_metadata == 8.5.0",
    'dataclasses == 0.8; python_version < "3.7.0"',
    "pytidylib == 0.3.2",
    "sphinx-autodoc-typehints == 2.0.1",
]

test_requires = [
    "selenium == 3.141.0",
    "nose2[coverage_plugin]==0.15.1",
    "pytest == 8.3.4",
    "pyvirtualdisplay",
    "coverage == 7.6.9"
]

doc_requires = [
    "sphinx == 7.1.2",
    "sphinx_rtd_theme == 1.0.0",
    "sphinx-tabs == 3.3.1",
    "ipython == 8.2.0"
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
