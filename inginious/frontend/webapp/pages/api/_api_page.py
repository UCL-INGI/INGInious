# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Helper classes and methods for the REST API """

import json

import web

import inginious.common.custom_yaml as yaml
from inginious.frontend.webapp.pages.utils import INGIniousPage


class APIPage(INGIniousPage):
    """ Generic handler for all API pages """

    def GET(self, *args, **kwargs):
        """ GET request """
        return self._handle_api(self.API_GET, args, kwargs)

    def PUT(self, *args, **kwargs):
        """ PUT request """
        return self._handle_api(self.API_PUT, args, kwargs)

    def POST(self, *args, **kwargs):
        """ POST request """
        return self._handle_api(self.API_POST, args, kwargs)

    def DELETE(self, *args, **kwargs):
        """ DELETE request """
        return self._handle_api(self.API_DELETE, args, kwargs)

    def PATCH(self, *args, **kwargs):
        """ PATCH request """
        return self._handle_api(self.API_PATCH, args, kwargs)

    def HEAD(self, *args, **kwargs):
        """ HEAD request """
        return self._handle_api(self.API_HEAD, args, kwargs)

    def OPTIONS(self, *args, **kwargs):
        """ OPTIONS request """
        return self._handle_api(self.API_OPTIONS, args, kwargs)

    def _handle_api(self, handler, handler_args, handler_kwargs):
        """ Handle call to subclasses and convert the output to an appropriate value """
        try:
            status_code, return_value = handler(*handler_args, **handler_kwargs)
        except APIError as error:
            return error.send()

        web.ctx.status = _convert_http_status(status_code)
        return _api_convert_output(return_value)

    def _guess_available_methods(self):
        """ Guess the method implemented by the subclass"""
        available_methods = []
        for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            self_method = getattr(type(self), "API_{}".format(m))
            super_method = getattr(APIPage, "API_{}".format(m))
            if self_method != super_method:
                available_methods.append(m)
        return available_methods

    def invalid_method(self):
        """ Returns 405 Invalid Method to the client """
        raise APIInvalidMethod(self._guess_available_methods())

    def API_GET(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API GET request. Should be overridden by subclasses """
        self.invalid_method()

    def API_PUT(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API PUT request. Should be overridden by subclasses """
        self.invalid_method()

    def API_POST(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API POST request. Should be overridden by subclasses """
        self.invalid_method()

    def API_DELETE(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API DELETE request. Should be overridden by subclasses """
        self.invalid_method()

    def API_PATCH(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API PATCH request. Should be overridden by subclasses """
        self.invalid_method()

    def API_HEAD(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API HEAD request. Should be overridden by subclasses """
        self.invalid_method()

    def API_OPTIONS(self, *args, **kwargs):  # pylint: disable=unused-argument
        """ API OPTIONS request. Should be overridden by subclasses """
        self.invalid_method()


class APIAuthenticatedPage(APIPage):
    """
        A wrapper for pages that needs authentification. Automatically checks that the client is authenticated and returns "403 Forbidden" if it's
        not the case.
    """

    def _handle_api(self, handler, handler_args, handler_kwargs):
        return APIPage._handle_api(self, (lambda *args, **kwargs: self._verify_authentication(handler, args, kwargs)), handler_args, handler_kwargs)

    def _verify_authentication(self, handler, args, kwargs):
        """ Verify that the user is authenticated """
        if not self.user_manager.session_logged_in():
            raise APIForbidden()
        return handler(*args, **kwargs)


class APIError(Exception):
    """ Standard API Error """

    def __init__(self, status_code, return_value):
        super(APIError, self).__init__()
        self.status_code = status_code
        self.return_value = return_value

    def send(self):
        """ Send the API Exception to the client """
        web.ctx.status = _convert_http_status(self.status_code)
        return _api_convert_output(self.return_value)


class APIInvalidMethod(APIError):
    """ Invalid method error """

    def __init__(self, methods):
        APIError.__init__(self, 405, {"error": "This endpoint has no such method"})
        self.methods = methods

    def send(self):
        web.header('Allow', ",".join(self.methods))
        return APIError.send(self)


class APIInvalidArguments(APIError):
    """ Invalid arguments error """

    def __init__(self):
        APIError.__init__(self, 400, {"error": "Invalid arguments for this method"})


class APIForbidden(APIError):
    """ Forbidden error """

    def __init__(self, message="You are not authenticated"):
        APIError.__init__(self, 403, {"error": message})


class APINotFound(APIError):
    """ Not found error """

    def __init__(self, message="Not found"):
        APIError.__init__(self, 404, {"error": message})


def _api_convert_output(return_value):
    """ Convert the output to what the client asks """
    content_type = web.ctx.environ.get('CONTENT_TYPE', 'text/json')

    if "text/json" in content_type:
        web.header('Content-Type', 'text/json; charset=utf-8')
        return json.dumps(return_value)
    if "text/html" in content_type:
        web.header('Content-Type', 'text/html; charset=utf-8')
        dump = yaml.dump(return_value)
        return "<pre>" + web.websafe(dump) + "</pre>"
    if "text/yaml" in content_type or \
                    "text/x-yaml" in content_type or \
                    "application/yaml" in content_type or \
                    "application/x-yaml" in content_type:
        web.header('Content-Type', 'text/yaml; charset=utf-8')
        dump = yaml.dump(return_value)
        return dump
    web.header('Content-Type', 'text/json; charset=utf-8')
    return json.dumps(return_value)


def _convert_http_status(status):
    """ Convert Status id to real Status needed by HTTP """
    return {
        200: "200 OK",
        201: "201 Created",
        202: "202 Accepted",
        203: "203 Non-Authoritative Information",
        204: "204 No Content",
        205: "205 Reset Content",
        206: "206 Partial Content",
        300: "300 Multiple Choices",
        301: "301 Moved Permanently",
        302: "302 Found",
        303: "303 See Other",
        304: "304 Not Modified",
        305: "305 Use Proxy",
        307: "307 Temporary Redirect",
        400: "400 Bad Request",
        401: "401 Unauthorized",
        403: "403 Forbidden",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
        406: "406 Not Acceptable",
        408: "408 Request Timeout",
        409: "409 Conflict",
        410: "410 Gone",
        412: "412 Precondition Failed",
        413: "413 Request Entity Too Large",
        500: "500 Internal Server Error",
        501: "501 Not Implemented"
    }.get(status)
