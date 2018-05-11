import posixpath
import urllib
import web

import inginious.frontend.pages.api._api_page as api
from inginious.frontend.pages.utils import INGIniousPage
from inginious.common.filesystems.local import LocalFSProvider


def get_mandatory_parameter(parameters, parameter_name):
    if parameter_name not in parameters:
        raise api.APIError(400, {"error": parameter_name + " is mandatory"})

    return parameters[parameter_name]


def create_static_resource_page(base_static_folder):
    class StaticResourcePage(INGIniousPage):
        def GET(self, path):
            path_norm = posixpath.normpath(urllib.parse.unquote(path))

            static_folder = LocalFSProvider(base_static_folder)
            (method, mimetype_or_none, file_or_url) = static_folder.distribute(path_norm, False)

            if method == "local":
                web.header('Content-Type', mimetype_or_none)
                return file_or_url
            elif method == "url":
                raise web.redirect(file_or_url)

            raise web.notfound()

    return StaticResourcePage
