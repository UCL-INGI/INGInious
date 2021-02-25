# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#

import os
import gettext
import builtins
from setuptools_scm import get_version

__version__ = get_version(fallback_version="0.7.dev0")

MARKETPLACE_URL = "https://marketplace.inginious.org/marketplace.json"


builtins.__dict__['_'] = gettext.gettext


def get_root_path():
    """ Returns the INGInious root path """
    return os.path.abspath(os.path.dirname(__file__))
