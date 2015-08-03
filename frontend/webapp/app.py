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
import threading

from gridfs import GridFS
from pymongo import MongoClient
import web

from backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from frontend.common import backend_interface
from frontend.webapp.database_updater import update_database
from frontend.common.plugin_manager import PluginManager
from common.course_factory import create_factories
from frontend.webapp.tasks import WebAppTask
from frontend.webapp.courses import WebAppCourse
from frontend.webapp.pages.utils import WebPyFakeMapping
from frontend.webapp.submission_manager import SubmissionManager
from frontend.webapp.batch_manager import BatchManager
from frontend.common.templates import TemplateHelper
from frontend.webapp.user_manager import UserManager
from frontend.common.session_mongodb import MongoStore
import frontend.webapp.pages.course_admin.utils as course_admin_utils

urls = {
    r'/': 'frontend.webapp.pages.index.IndexPage',
    r'/index': 'frontend.webapp.pages.index.IndexPage',
    r'/course/([^/]+)': 'frontend.webapp.pages.course.CoursePage',
    r'/course/([^/]+)/([^/]+)': 'frontend.webapp.pages.tasks.TaskPage',
    r'/course/([^/]+)/([^/]+)/(.*)': 'frontend.webapp.pages.tasks.TaskPageStaticDownload',
    r'/group/([^/]+)': 'frontend.webapp.pages.group.GroupPage',
    r'/admin/([^/]+)': 'frontend.webapp.pages.course_admin.utils.CourseRedirect',
    r'/admin/([^/]+)/settings': 'frontend.webapp.pages.course_admin.settings.CourseSettings',
    r'/admin/([^/]+)/batch': 'frontend.webapp.pages.course_admin.batch.CourseBatchOperations',
    r'/admin/([^/]+)/batch/create/(.+)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobCreate',
    r'/admin/([^/]+)/batch/summary/([^/]+)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobSummary',
    r'/admin/([^/]+)/batch/download/([^/]+)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobDownload',
    r'/admin/([^/]+)/batch/download/([^/]+)(/.*)': 'frontend.webapp.pages.course_admin.batch.CourseBatchJobDownload',
    r'/admin/([^/]+)/students': 'frontend.webapp.pages.course_admin.student_list.CourseStudentListPage',
    r'/admin/([^/]+)/student/([^/]+)': 'frontend.webapp.pages.course_admin.student_info.CourseStudentInfoPage',
    r'/admin/([^/]+)/student/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.student_task.CourseStudentTaskPage',
    r'/admin/([^/]+)/student/([^/]+)/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.student_task.SubmissionDownloadFeedback',
    r'/admin/([^/]+)/classrooms': 'frontend.webapp.pages.course_admin.classroom_list.CourseClassroomListPage',
    r'/admin/([^/]+)/classroom/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_info.CourseClassroomInfoPage',
    r'/admin/([^/]+)/classroom/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_task.CourseClassroomTaskPage',
    r'/admin/([^/]+)/classroom/([^/]+)/([^/]+)/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_task.SubmissionDownloadFeedback',
    r'/admin/([^/]+)/tasks': 'frontend.webapp.pages.course_admin.task_list.CourseTaskListPage',
    r'/admin/([^/]+)/task/([^/]+)': 'frontend.webapp.pages.course_admin.task_info.CourseTaskInfoPage',
    r'/admin/([^/]+)/edit/classroom/([^/]+)': 'frontend.webapp.pages.course_admin.classroom_edit.CourseEditClassroom',
    r'/admin/([^/]+)/edit/task/([^/]+)': 'frontend.webapp.pages.course_admin.task_edit.CourseEditTask',
    r'/admin/([^/]+)/edit/task/([^/]+)/files': 'frontend.webapp.pages.course_admin.task_edit_file.CourseTaskFiles',
    r'/admin/([^/]+)/download': 'frontend.webapp.pages.course_admin.download.CourseDownloadSubmissions',
    r'/api/v0/auth_methods': 'frontend.webapp.pages.api.auth_methods.APIAuthMethods',
    r'/api/v0/authentication': 'frontend.webapp.pages.api.authentication.APIAuthentication',
    r'/api/v0/courses': 'frontend.webapp.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)': 'frontend.webapp.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks': 'frontend.webapp.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)': 'frontend.webapp.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions': 'frontend.webapp.pages.api.submissions.APISubmissions',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)':
        'frontend.webapp.pages.api.submissions.APISubmissionSingle',
}

urls_maintenance = (
    '/.*', 'webapp.pages.maintenance.MaintenancePage'
)


def _put_configuration_defaults(config):
    """
    :param config: the basic configuration as a dict
    :return: the same dict, but with defaults for some unfilled parameters
    """
    if 'allowed_file_extensions' not in config:
        config['allowed_file_extensions'] = [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"]
    if 'max_file_size' not in config:
        config['max_file_size'] = 1024 * 1024
    return config


def _close_app(app, mongo_client, job_manager):
    """ Ensures that the app is properly closed """
    app.stop()
    job_manager.close()
    mongo_client.close()


def _handle_active_hook(job_manager, plugin_manager, active_callback):
    """
    Creates the necessary hooks in plugin_manager and ensures active_callback will be called at the right time
    :param job_manager:
    :param plugin_manager:
    :param active_callback:
    """
    sync_mutex = threading.Lock()
    #start_mutex = threading.Lock()
    def sync_done(check_all_done):
        """ release """
        sync_mutex.acquire()
        sync_done.done = True
        sync_mutex.release()
        check_all_done()


    #def start_done(check_all_done):
    #    """ release """
    #    start_mutex.acquire()
    #    start_done.done = True
    #    start_mutex.release()
    #    check_all_done()

    sync_done.done = False
    #start_done.done = False

    def check_all_done():
        sync_mutex.acquire()
        #start_mutex.acquire()
        if sync_done.done:# and start_done.done:
            try:
                active_callback()
            except:
                pass
        sync_mutex.release()
        #start_mutex.release()

    if not isinstance(job_manager, RemoteManualAgentJobManager):
        sync_done.done = True

    plugin_manager.add_hook("job_manager_agent_sync_done", lambda agent: sync_done(check_all_done))
    #plugin_manager.add_hook("job_manager_init_done", lambda job_manager: start_done(check_all_done))
    check_all_done()


def get_app(config, active_callback=None):
    """
    :param config: the configuration dict
    :param active_callback: a callback without arguments that will be called when the app is fully initialized
    :return: A new app
    """
    config = _put_configuration_defaults(config)

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

    course_factory, task_factory = create_factories(task_directory, plugin_manager, WebAppCourse, WebAppTask)

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

    # Active hook
    if active_callback is not None:
        _handle_active_hook(job_manager, plugin_manager, active_callback)

    # Loads plugins
    plugin_manager.load(job_manager, appli, course_factory, task_factory, user_manager, config.get("plugins", []))

    # Start the backend
    job_manager.start()

    return appli, lambda: _close_app(appli, mongo_client, job_manager)


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
        """ Normalize the path """
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2


def runfcgi(func, addr=('localhost', 8000)):
    """Runs a WSGI function as a FastCGI server."""
    import flup.server.fcgi as flups

    return flups.WSGIServer(func, multiplexed=True, bindAddress=addr, debug=False).run()


def start_app(config, hostname="localhost", port=8080):
    """
        Get and start the application. config_file is the path to the configuration file.
    """
    app, close_app_func = get_app(config)

    func = app.wsgifunc()

    if 'SERVER_SOFTWARE' in os.environ:  # cgi
        os.environ['FCGI_FORCE_CGI'] = 'Y'

    if 'PHP_FCGI_CHILDREN' in os.environ or 'SERVER_SOFTWARE' in os.environ:  # lighttpd fastcgi
        return runfcgi(func, None)

    # Close the job manager when interrupting the app
    def close_app_signal():
        close_app_func()
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, lambda _, _2: close_app_signal)

    func = StaticMiddleware(func)
    func = web.httpserver.LogMiddleware(func)
    server = web.httpserver.WSGIServer((hostname, port), func)
    print "http://%s:%d/" % (hostname, port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
