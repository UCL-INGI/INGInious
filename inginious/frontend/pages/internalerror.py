# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Internal error page """
from web import HTTPError


class InternalError(HTTPError):
    """500 Internal Server Error`."""
    def __init__(self, message):
        status = '500 Internal Server Error'
        headers = {'Content-Type': 'text/html'}
        HTTPError.__init__(self, status, headers, message)

def internalerror_generator(renderer):
    """ Returns a function which will include the message inside the inginious template """
    return lambda message=None: InternalError(renderer.internalerror(message))