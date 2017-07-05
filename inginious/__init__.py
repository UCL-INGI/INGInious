# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#

import os

__version__ = "0.5.dev0"


def get_root_path():
    """ Returns the INGInious root path """
    return os.path.abspath(os.path.dirname(__file__))
