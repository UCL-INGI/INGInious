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
import signal

from gridfs import GridFS
from pymongo import MongoClient
import web

from common.base import load_json_or_yaml
from frontend.common import backend_interface
from frontend.webapp.database_updater import update_database
from frontend.common.plugin_manager import PluginManager
from common.course_factory import create_factories
from frontend.webapp.custom.tasks import FrontendTask
from frontend.webapp.custom.courses import FrontendCourse
from frontend.webapp.pages.utils import WebPyFakeMapping
from frontend.webapp.submission_manager import SubmissionManager
from frontend.webapp.batch_manager import BatchManager
from frontend.common.templates import TemplateHelper
from frontend.webapp.user_manager import UserManager
from frontend.common.session_mongodb import MongoStore
import frontend.webapp.pages.course_admin.utils as course_admin_utils

urls = {
    '/': 'frontend.webapp.pages.index.IndexPage',
    '/index': 'frontend.webapp.pages.index.IndexPage',
    '/course/([^/]+)': 'frontend.webapp.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)': 'frontend.webapp.pages.tasks.TaskPage',
    '/course/([^/]+)/([^/]+)/(.*)': 'frontend.webapp.pages.tasks.TaskPageStaticDownload',
    '/group/([^/]+)': 'frontend.webapp.pages.group.GroupPage',
    '/admin/([^/]+)': 'frontend.webapp.pages.course_admin.utils.CourseRedirect',
    '/admin/([^/]+)/settings': 'frontend.webapp.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/batch': 'frontend.webapp.pages.course_admin.batch.CourseBatchOperations',
    '/admin/([^/]+)/batch/create/(.+)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobCreate',
    '/admin/([^/]+)/batch/summary/([^/]+)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobSummary',
    '/admin/([^/]+)/batch/download/([^/]+)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobDownload',
    '/admin/([^/]+)/batch/download/([^/]+)(/.*)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobDownload',
    '/admin/([^/]+)/students': 'frontend.webapp.pages.course_admin.student_list.CourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)': 'frontend.webapp.pages.course_admin.student_info.CourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.student_task.CourseStudentTaskPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.student_task.SubmissionDownloadFeedback',
    '/admin/([^/]+)/classrooms': 'frontend.webapp.pages.course_admin.classroom_list.CourseClassroomListPage',
    '/admin/([^/]+)/classroom/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_info.CourseGroupInfoPage',
    '/admin/([^/]+)/classroom/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_task.CourseGroupTaskPage',
    '/admin/([^/]+)/classroom/([^/]+)/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_task.SubmissionDownloadFeedback',
    '/admin/([^/]+)/tasks': 'frontend.webapp.pages.course_admin.task_list.CourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)': 'frontend.webapp.pages.course_admin.task_info.CourseTaskInfoPage',
    '/admin/([^/]+)/edit/classroom/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_edit.CourseEditGroup',
    '/admin/([^/]+)/edit/task/([^/]+)': 'frontend.webapp.pages.course_admin.task_edit.CourseEditTask',
    '/admin/([^/]+)/edit/task/([^/]+)/files': 'frontend.webapp.pages.course_admin.task_edit_file.CourseTaskFiles',
    '/admin/([^/]+)/download': 'frontend.webapp.pages.course_admin.download.CourseDownloadSubmissions',
    '/api/v0/auth_methods': 'frontend.webapp.pages.api.auth_methods.APIAuthMethods',
    '/api/v0/authentication': 'frontend.webapp.pages.api.authentication.APIAuthentication',
    '/api/v0/courses': 'frontend.webapp.pages.api.courses.APICourses',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)': 'frontend.webapp.pages.api.courses.APICourses',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks': 'frontend.webapp.pages.api.tasks.APITasks',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)': 'frontend.webapp.pages.api.tasks.APITasks',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions': 'frontend.webapp.pages.api.submissions.APISubmissions',
    '/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)':
        'frontend.webapp.pages.api.submissions.APISubmissionSingle',
}

urls_maintenance = (
    '/.*', 'webapp.pages.maintenance.MaintenancePage'
)


def _load_configuration(config_file):
    """
    :param config_file:
    :return: a dict containing the configuration
    """
    config = load_json_or_yaml(config_file)
    if not 'allowed_file_extensions' in config:
        config['allowed_file_extensions'] = [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"]
    if not 'max_file_size' in config:
        config['max_file_size'] = 1024 * 1024
    return config

def _close_app(app, mongo_client, job_manager):
    app.stop()
    job_manager.close()
    mongo_client.close()
    raise KeyboardInterrupt()

def get_app(config_file):
    """ Get the application. config_file is the path to the configuration file """
    config = _load_configuration(config_file)

    if config.get("maintenance", False):
        appli = web.application(urls_maintenance, globals(), autoreload=False)
        return appli

    task_directory = config["tasks_directory"]
    default_allowed_file_extensions = config['allowed_file_extensions']
    default_max_file_size = config['max_file_size']

    appli = web.application((), globals(), autoreload=False)

    # Init the different parts of the app
    plugin_manager = PluginManager()

    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]
    gridfs = GridFS(database)

    course_factory, task_factory = create_factories(task_directory, plugin_manager, FrontendCourse, FrontendTask)

    user_manager = UserManager(web.session.Session(appli, MongoStore(database, 'sessions')), database, config.get('superadmins', []))

    backend_interface.update_pending_jobs(database)

    job_manager = backend_interface.create_job_manager(config, plugin_manager,
                                                       task_directory, course_factory, task_factory)

    submission_manager = SubmissionManager(job_manager, user_manager, database, gridfs, plugin_manager)

    batch_manager = BatchManager(job_manager, database, gridfs, submission_manager, user_manager,
                                 task_directory, config.get('batch_containers', []),
                                 config.get('smtp', None))

    template_helper = TemplateHelper(plugin_manager, 'frontend/webapp/templates', 'layout')

    # Update the database
    update_database(database, gridfs, course_factory, user_manager)

    # Add some helpers for the templates
    template_helper.add_to_template_globals("user_manager", user_manager)
    template_helper.add_to_template_globals("default_allowed_file_extensions", default_allowed_file_extensions)
    template_helper.add_to_template_globals("default_max_file_size", default_max_file_size)
    template_helper.add_other("course_admin_menu",
                              lambda course, current: course_admin_utils.get_menu(course, current, template_helper.get_renderer(False),
                                                                                  plugin_manager, user_manager))

    # Not found page
    appli.notfound = lambda: web.notfound(template_helper.get_renderer().notfound('Page not found'))

    # Init the mapping of the app
    appli.mapping = WebPyFakeMapping(dict(urls), plugin_manager,
                                     course_factory, task_factory,
                                     submission_manager, batch_manager, user_manager,
                                     template_helper, database, gridfs,
                                     default_allowed_file_extensions, default_max_file_size,
                                     config["containers"].keys())

    # Loads plugins
    plugin_manager.load(job_manager, appli, course_factory, task_factory, user_manager, config.get("plugins", []))

    # Start the backend
    job_manager.start()

    # Close the job manager when interrupting the app
    signal.signal(signal.SIGINT, lambda _, _2: _close_app(appli, mongo_client, job_manager))

    return appli


class StaticMiddleware(object):
    """ WSGI middleware for serving static files. """

    def __init__(self, app, prefix='/static/', root_path='frontend/webapp/static'):
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
