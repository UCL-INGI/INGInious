# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Starts the frontend """

import posixpath
import urllib

import web

from frontend import backend_interface
import frontend.base
import frontend.configuration
from frontend.database_updater import update_database
from frontend.plugins.plugin_manager import PluginManager
import frontend.session
import os
import sys
from frontend.template_helper import TemplateHelper

urls = (
    '/', 'frontend.pages.index.IndexPage',
    '/index', 'frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'frontend.pages.tasks.TaskPage',
    '/course/([^/]+)/([^/]+)/(.*)', 'frontend.pages.tasks.TaskPageStaticDownload',
    '/group/([^/]+)', 'frontend.pages.group.GroupPage',
    '/admin/([^/]+)', 'frontend.pages.course_admin.utils.CourseRedirect',
    '/admin/([^/]+)/settings', 'frontend.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/batch', 'frontend.pages.course_admin.batch.CourseBatchOperations',
    '/admin/([^/]+)/batch/create/(.+)', 'frontend.pages.course_admin.batch.CourseBatchJobCreate',
    '/admin/([^/]+)/batch/summary/([^/]+)', 'frontend.pages.course_admin.batch.CourseBatchJobSummary',
    '/admin/([^/]+)/batch/download/([^/]+)', 'frontend.pages.course_admin.batch.CourseBatchJobDownload',
    '/admin/([^/]+)/batch/download/([^/]+)(/.*)', 'frontend.pages.course_admin.batch.CourseBatchJobDownload',
    '/admin/([^/]+)/students', 'frontend.pages.course_admin.student_list.CourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)', 'frontend.pages.course_admin.student_info.CourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)', 'frontend.pages.course_admin.student_task.CourseStudentTaskPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)/([^/]+)', 'frontend.pages.course_admin.student_task.SubmissionDownloadFeedback',
    '/admin/([^/]+)/groups', 'frontend.pages.course_admin.group_list.CourseGroupListPage',
    '/admin/([^/]+)/tasks', 'frontend.pages.course_admin.task_list.CourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)', 'frontend.pages.course_admin.task_info.CourseTaskInfoPage',
    '/admin/([^/]+)/edit/group/([^/]+)', 'frontend.pages.course_admin.group_edit.CourseEditGroup',
    '/admin/([^/]+)/edit/task/([^/]+)', 'frontend.pages.course_admin.task_edit.CourseEditTask',
    '/admin/([^/]+)/edit/task/([^/]+)/files', 'frontend.pages.course_admin.task_edit_file.CourseTaskFiles',
    '/admin/([^/]+)/submissions', 'frontend.pages.course_admin.submission_files.DownloadSubmissionFiles',

)

urls_maintenance = (
    '/.*', 'frontend.pages.maintenance.MaintenancePage'
)


def get_app(config_file):
    """ Get the application. config_file is the path to the configuration file """
    frontend.configuration.INGIniousConfiguration.load(config_file)
    if frontend.configuration.INGIniousConfiguration.get("maintenance", False):
        appli = web.application(urls_maintenance, globals(), autoreload=False)
        return appli

    appli = web.application(urls, globals(), autoreload=False)

    frontend.base.init_database()
    update_database()
    frontend.session.init(appli)

    def not_found():
        """ Display the error 404 page """
        return web.notfound(frontend.base.renderer.notfound('Page not found'))

    appli.notfound = not_found

    plugin_manager = PluginManager(appli, frontend.configuration.INGIniousConfiguration.get("plugins", []))

    # Plugin Manager is also a Hook Manager
    backend_interface.init(plugin_manager)

    # Loads template_helper
    TemplateHelper()

    # Loads plugins
    plugin_manager.load()

    # Start the backend
    backend_interface.start()

    return appli


class StaticMiddleware(object):
    """ WSGI middleware for serving static files. """

    def __init__(self, app, prefix='/static/', root_path='frontend/static'):
        self.app = app
        self.prefix = prefix
        self.root_path = root_path

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)

        if path.startswith(self.prefix):
            environ["PATH_INFO"] = self.root_path + "/" + web.lstrips(path, self.prefix)
            return web.httpserver.StaticApp(environ, start_response)
        else:
            return self.app(environ, start_response)

    def normpath(self, path):
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2


def runfcgi(func, addr=('localhost', 8000)):
    """Runs a WSGI function as a FastCGI server."""
    import flup.server.fcgi as flups

    return flups.WSGIServer(func, multiplexed=True, bindAddress=addr, debug=False).run()

def start_app(config_file, hostname="localhost", port=8080, app=None):
    """
        Get and start the application. config_file is the path to the configuration file.
    """
    if app is None:
        app = get_app(config_file)

    func = app.wsgifunc()

    if os.environ.has_key('SERVER_SOFTWARE'):  # cgi
        os.environ['FCGI_FORCE_CGI'] = 'Y'

    if (os.environ.has_key('PHP_FCGI_CHILDREN')  # lighttpd fastcgi
        or os.environ.has_key('SERVER_SOFTWARE')):
        return runfcgi(func, None)

    func = StaticMiddleware(func)
    func = web.httpserver.LogMiddleware(func)
    server = web.httpserver.WSGIServer((hostname, port), func)
    print "http://%s:%d/" % (hostname, port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
