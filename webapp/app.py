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
""" Starts the webapp """

import posixpath
import urllib
import os

import web

import common_frontend.database
from common_frontend import backend_interface
import common_frontend.templates
import common_frontend.configuration
from webapp.database_updater import update_database
from common_frontend.plugin_manager import PluginManager
from common.course_factory import create_factories
import common_frontend.templates
import common_frontend.session
import webapp.pages.course_admin.utils
from webapp.custom.tasks import FrontendTask
from webapp.custom.courses import FrontendCourse
from webapp.pages.utils import webpy_fake_class_creator

urls = {
    '/': 'webapp.pages.index.IndexPage',
    '/index': 'webapp.pages.index.IndexPage',
    '/course/([^/]+)': 'webapp.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)': 'webapp.pages.tasks.TaskPage',
    '/course/([^/]+)/([^/]+)/(.*)': 'webapp.pages.tasks.TaskPageStaticDownload',
    '/group/([^/]+)': 'webapp.pages.group.GroupPage',
    '/admin/([^/]+)': 'webapp.pages.course_admin.utils.CourseRedirect',
    '/admin/([^/]+)/settings': 'webapp.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/batch': 'webapp.pages.course_admin.batch.CourseBatchOperations',
    '/admin/([^/]+)/batch/create/(.+)': 'webapp.pages.course_admin.batch.CourseBatchJobCreate',
    '/admin/([^/]+)/batch/summary/([^/]+)': 'webapp.pages.course_admin.batch.CourseBatchJobSummary',
    '/admin/([^/]+)/batch/download/([^/]+)': 'webapp.pages.course_admin.batch.CourseBatchJobDownload',
    '/admin/([^/]+)/batch/download/([^/]+)(/.*)': 'webapp.pages.course_admin.batch.CourseBatchJobDownload',
    '/admin/([^/]+)/students': 'webapp.pages.course_admin.student_list.CourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)': 'webapp.pages.course_admin.student_info.CourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)': 'webapp.pages.course_admin.student_task.CourseStudentTaskPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)/([^/]+)': 'webapp.pages.course_admin.student_task.SubmissionDownloadFeedback',
    '/admin/([^/]+)/groups': 'webapp.pages.course_admin.group_list.CourseGroupListPage',
    '/admin/([^/]+)/group/([^/]+)': 'webapp.pages.course_admin.group_info.CourseGroupInfoPage',
    '/admin/([^/]+)/group/([^/]+)/([^/]+)': 'webapp.pages.course_admin.group_task.CourseGroupTaskPage',
    '/admin/([^/]+)/group/([^/]+)/([^/]+)/([^/]+)': 'webapp.pages.course_admin.group_task.SubmissionDownloadFeedback',
    '/admin/([^/]+)/tasks': 'webapp.pages.course_admin.task_list.CourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)': 'webapp.pages.course_admin.task_info.CourseTaskInfoPage',
    '/admin/([^/]+)/edit/group/([^/]+)': 'webapp.pages.course_admin.group_edit.CourseEditGroup',
    '/admin/([^/]+)/edit/task/([^/]+)': 'webapp.pages.course_admin.task_edit.CourseEditTask',
    '/admin/([^/]+)/edit/task/([^/]+)/files': 'webapp.pages.course_admin.task_edit_file.CourseTaskFiles',
    '/admin/([^/]+)/download': 'webapp.pages.course_admin.download.CourseDownloadSubmissions',
    '/api/v0/auth_methods': 'webapp.pages.api.auth_methods.APIAuthMethods',
    '/api/v0/authentication': 'webapp.pages.api.authentication.APIAuthentication',
    '/api/v0/courses': 'webapp.pages.api.courses.APICourses',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)': 'webapp.pages.api.courses.APICourses',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks': 'webapp.pages.api.tasks.APITasks',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)': 'webapp.pages.api.tasks.APITasks',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions': 'webapp.pages.api.submissions.APISubmissions',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)':
        'webapp.pages.api.submissions.APISubmissionSingle',
}

urls_maintenance = (
    '/.*', 'webapp.pages.maintenance.MaintenancePage'
)


def get_app(config_file):
    """ Get the application. config_file is the path to the configuration file """
    common_frontend.configuration.INGIniousConfiguration.load(config_file)
    if common_frontend.configuration.INGIniousConfiguration.get("maintenance", False):
        appli = web.application(urls_maintenance, globals(), autoreload=False)
        return appli

    appli = web.application((), globals(), autoreload=False)

    course_factory, task_factory = create_factories(common_frontend.configuration.INGIniousConfiguration["tasks_directory"], FrontendCourse,
                                                    FrontendTask)

    common_frontend.database.init_database()
    update_database(course_factory)
    common_frontend.session.init(appli)

    def not_found():
        """ Display the error 404 page """
        return web.notfound(common_frontend.templates.get_renderer().notfound('Page not found'))

    appli.notfound = not_found

    plugin_manager = PluginManager(appli, course_factory, task_factory, common_frontend.configuration.INGIniousConfiguration.get("plugins", []))

    # Plugin Manager is also a Hook Manager
    backend_interface.init(plugin_manager, course_factory, task_factory)

    # Init templates
    common_frontend.templates.init_renderer('webapp/templates', 'layout')
    common_frontend.templates.TemplateHelper().add_other("course_admin_menu", webapp.pages.course_admin.utils.get_menu)

    # Init the mapping of the app
    fixed_urls = dict(urls)
    for key, val in fixed_urls.iteritems():
        fixed_urls[key] = webpy_fake_class_creator(val, plugin_manager, course_factory, task_factory)
    appli.init_mapping([item for sublist in fixed_urls.iteritems() for item in sublist])

    # Loads plugins
    plugin_manager.load()

    # Start the backend
    backend_interface.start()

    # Configure Web.py
    if "smtp" in common_frontend.configuration.INGIniousConfiguration:
        config_smtp = common_frontend.configuration.INGIniousConfiguration["smtp"]
        web.config.smtp_server = config_smtp["host"]
        web.config.smtp_port = int(config_smtp["port"])
        web.config.smtp_starttls = bool(config_smtp["starttls"])
        web.config.smtp_username = config_smtp["username"]
        web.config.smtp_password = config_smtp["password"]
    return appli


class StaticMiddleware(object):
    """ WSGI middleware for serving static files. """

    def __init__(self, app, prefix='/static/', root_path='webapp/static'):
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
