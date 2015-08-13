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

from inginious.backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from inginious.frontend.common import backend_interface
from inginious.frontend.common.static_middleware import StaticMiddleware
from inginious.frontend.common.webpy_fake_mapping import WebPyCustomMapping
from inginious.frontend.webapp.database_updater import update_database
from inginious.frontend.common.plugin_manager import PluginManager
from inginious.common.course_factory import create_factories
from inginious.frontend.webapp.remote_ssh_manager import RemoteSSHManager
from inginious.frontend.webapp.tasks import WebAppTask
from inginious.frontend.webapp.courses import WebAppCourse
from inginious.frontend.webapp.submission_manager import WebAppSubmissionManager
from inginious.frontend.webapp.batch_manager import BatchManager
from inginious.frontend.common.templates import TemplateHelper
from inginious.frontend.webapp.user_manager import UserManager
from inginious.frontend.common.session_mongodb import MongoStore
import inginious.frontend.webapp.pages.course_admin.utils as course_admin_utils

urls = {
    r'/': 'inginious.frontend.webapp.pages.index.IndexPage',
    r'/index': 'inginious.frontend.webapp.pages.index.IndexPage',
    r'/course/([^/]+)': 'inginious.frontend.webapp.pages.course.CoursePage',
    r'/course/([^/]+)/([^/]+)': 'inginious.frontend.webapp.pages.tasks.TaskPage',
    r'/course/([^/]+)/([^/]+)/(.*)': 'inginious.frontend.webapp.pages.tasks.TaskPageStaticDownload',
    r'/classroom/([^/]+)': 'inginious.frontend.webapp.pages.classroom.ClassroomPage',
    r'/admin/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.utils.CourseRedirect',
    r'/admin/([^/]+)/settings': 'inginious.frontend.webapp.pages.course_admin.settings.CourseSettings',
    r'/admin/([^/]+)/batch': 'inginious.frontend.webapp.pages.course_admin.batch.CourseBatchOperations',
    r'/admin/([^/]+)/batch/create/(.+)': 'inginious.frontend.webapp.pages.course_admin.batch.CourseBatchJobCreate',
    r'/admin/([^/]+)/batch/summary/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.batch.CourseBatchJobSummary',
    r'/admin/([^/]+)/batch/download/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.batch.CourseBatchJobDownload',
    r'/admin/([^/]+)/batch/download/([^/]+)(/.*)': 'inginious.frontend.webapp.pages.course_admin.batch.CourseBatchJobDownload',
    r'/admin/([^/]+)/students': 'inginious.frontend.webapp.pages.course_admin.student_list.CourseStudentListPage',
    r'/admin/([^/]+)/student/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.student_info.CourseStudentInfoPage',
    r'/admin/([^/]+)/student/([^/]+)/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.student_task.CourseStudentTaskPage',
    r'/admin/([^/]+)/student/([^/]+)/([^/]+)/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.submission.CourseStudentTaskSubmission',
    r'/admin/([^/]+)/classrooms': 'inginious.frontend.webapp.pages.course_admin.classroom_list.CourseClassroomListPage',
    r'/admin/([^/]+)/classroom/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.classroom_info.CourseClassroomInfoPage',
    r'/admin/([^/]+)/classroom/([^/]+)/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.classroom_task.CourseClassroomTaskPage',
    r'/admin/([^/]+)/classroom/([^/]+)/([^/]+)/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.classroom_task.SubmissionDownloadFeedback',
    r'/admin/([^/]+)/tasks': 'inginious.frontend.webapp.pages.course_admin.task_list.CourseTaskListPage',
    r'/admin/([^/]+)/task/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.task_info.CourseTaskInfoPage',
    r'/admin/([^/]+)/edit/classroom/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.classroom_edit.CourseEditClassroom',
    r'/admin/([^/]+)/edit/task/([^/]+)': 'inginious.frontend.webapp.pages.course_admin.task_edit.CourseEditTask',
    r'/admin/([^/]+)/edit/task/([^/]+)/files': 'inginious.frontend.webapp.pages.course_admin.task_edit_file.CourseTaskFiles',
    r'/admin/([^/]+)/download': 'inginious.frontend.webapp.pages.course_admin.download.CourseDownloadSubmissions',
    r'/api/v0/auth_methods': 'inginious.frontend.webapp.pages.api.auth_methods.APIAuthMethods',
    r'/api/v0/authentication': 'inginious.frontend.webapp.pages.api.authentication.APIAuthentication',
    r'/api/v0/courses': 'inginious.frontend.webapp.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)': 'inginious.frontend.webapp.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks': 'inginious.frontend.webapp.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)': 'inginious.frontend.webapp.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions': 'inginious.frontend.webapp.pages.api.submissions.APISubmissions',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)':
        'inginious.frontend.webapp.pages.api.submissions.APISubmissionSingle',
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


def _close_app(app, mongo_client, job_manager, remote_ssh_manager):
    """ Ensures that the app is properly closed """
    app.stop()
    remote_ssh_manager.stop()
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
    def sync_done(check_all_done):
        """ release """
        sync_mutex.acquire()
        sync_done.done = True
        sync_mutex.release()
        check_all_done()

    sync_done.done = False

    def check_all_done():
        sync_mutex.acquire()
        if sync_done.done:
            try:
                active_callback()
            except:
                pass
        sync_mutex.release()

    if not isinstance(job_manager, RemoteManualAgentJobManager):
        sync_done.done = True

    plugin_manager.add_hook("job_manager_agent_sync_done", lambda agent: sync_done(check_all_done))
    check_all_done()


def get_app(hostname, port, sshhost, sshport, config, active_callback=None):
    """
    :param hostname: the hostname on which the web app will be bound
    :param port: the port on which the web app will be bound
    :param sshport: the port on which remote container debugging clients will connect
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

    remote_ssh_manager = RemoteSSHManager(sshhost, sshport, database, job_manager)

    if config.get("remote_debugging_active", True) and job_manager.is_remote_debug_active():
        if sshhost is None:
            print "You have to set the --sshhost arg to start the remote debugging manager. Remote debugging is then deactivated"
        else:
            remote_ssh_manager.start()

    submission_manager = WebAppSubmissionManager(job_manager, user_manager, database, gridfs, plugin_manager)

    batch_manager = BatchManager(job_manager, database, gridfs, submission_manager, user_manager,
                                 task_directory, config.get('batch_containers', []))

    template_helper = TemplateHelper(plugin_manager, 'frontend/webapp/templates', 'layout', config.get('use_minified_js', True))

    # Init web mail
    smtp_conf = config.get('smtp', None)
    if smtp_conf is not None:
        web.config.smtp_server = smtp_conf["host"]
        web.config.smtp_port = int(smtp_conf["port"])
        web.config.smtp_starttls = bool(smtp_conf.get("starttls", False))
        web.config.smtp_username = smtp_conf.get("username", "")
        web.config.smtp_password = smtp_conf.get("password", "")
        web.config.smtp_sendername = smtp_conf.get("sendername", "no-reply@ingnious.org")

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
    appli.init_mapping(WebPyCustomMapping(dict(urls), plugin_manager,
                                        course_factory, task_factory,
                                        submission_manager, batch_manager, user_manager,
                                        remote_ssh_manager, template_helper, database, gridfs,
                                        default_allowed_file_extensions, default_max_file_size,
                                        config["containers"].keys()))

    # Active hook
    if active_callback is not None:
        _handle_active_hook(job_manager, plugin_manager, active_callback)

    # Loads plugins
    plugin_manager.load(job_manager, appli, course_factory, task_factory, database, user_manager, config.get("plugins", []))

    # Start the inginious.backend
    job_manager.start()

    return appli, lambda: _close_app(appli, mongo_client, job_manager, remote_ssh_manager)

def runfcgi(func, addr=('localhost', 8000)):
    """Runs a WSGI function as a FastCGI server."""
    import flup.server.fcgi as flups

    return flups.WSGIServer(func, multiplexed=True, bindAddress=addr, debug=False).run()


def start_app(config, hostname="localhost", port=8080, sshhost=None, sshport=8081):
    """
    :type config: collections.OrderedDict
    :type hostname: str
    :type port: int
    :param sshhost:
    :type sshport: int
    :return:
    """
    app, close_app_func = get_app(hostname, port, sshhost, sshport, config)

    func = app.wsgifunc()

    if 'SERVER_SOFTWARE' in os.environ:  # cgi
        os.environ['FCGI_FORCE_CGI'] = 'Y'

    if 'PHP_FCGI_CHILDREN' in os.environ or 'SERVER_SOFTWARE' in os.environ:  # lighttpd fastcgi
        return runfcgi(func, None)

    # Close the job manager when interrupting the app
    def close_app_signal():
        close_app_func()
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, lambda _, _2: close_app_signal())
    signal.signal(signal.SIGTERM, lambda _, _2: close_app_signal())

    inginious_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    func = StaticMiddleware(func, (
        ('/static/common/', os.path.join(inginious_root_path, 'frontend', 'common', 'static')),
        ('/static/webapp/', os.path.join(inginious_root_path, 'frontend', 'webapp', 'static'))
    ))
    func = web.httpserver.LogMiddleware(func)
    server = web.httpserver.WSGIServer((hostname, port), func)
    print "http://%s:%d/" % (hostname, port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
