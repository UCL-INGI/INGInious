# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#

import os
import gettext
import builtins

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "0.7.dev0"

MARKETPLACE_URL = "https://marketplace.inginious.org/marketplace.json"
DB_VERSION = 15

builtins.__dict__['_'] = gettext.gettext


def get_root_path():
    """ Returns the INGInious root path """
    return os.path.abspath(os.path.dirname(__file__))
