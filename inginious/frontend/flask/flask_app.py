# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from werkzeug.routing import BaseConverter


class CookielessConverter(BaseConverter):
    # Parse the cookieless sessionid at the beginning of the url
    regex = r"((@)([a-f0-9A-F_]*)(@/))?"

    def to_python(self, value):
        return value[1:-2]

    def to_url(self, value):
        return "@" + str(value) + "@/"