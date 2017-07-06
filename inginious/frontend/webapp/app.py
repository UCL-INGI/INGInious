# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Starts the webapp """
from gridfs import GridFS
from pymongo import MongoClient
import web
from web.debugerror import debugerror

from inginious.frontend.common.arch_helper import create_arch, start_asyncio_and_zmq
from inginious.frontend.webapp.database_updater import update_database
from inginious.frontend.common.plugin_manager import PluginManager
from inginious.common.course_factory import create_factories
from inginious.frontend.webapp.tasks import WebAppTask
from inginious.frontend.webapp.courses import WebAppCourse
from inginious.frontend.webapp.submission_manager import WebAppSubmissionManager
from inginious.frontend.common.template_helper import TemplateHelper
from inginious.frontend.webapp.user_manager import UserManager
from inginious.frontend.common.session_mongodb import MongoStore
import inginious.frontend.webapp.pages.course_admin.utils as course_admin_utils
from inginious.frontend.common.submission_manager import update_pending_jobs

urls = (
    r'/', 'inginious.frontend.webapp.pages.index.IndexPage',
    r'/index', 'inginious.frontend.webapp.pages.index.IndexPage',
    r'/course/([^/]+)', 'inginious.frontend.webapp.pages.course.CoursePage',
    r'/course/([^/]+)/([^/]+)', 'inginious.frontend.webapp.pages.tasks.TaskPage',
    r'/course/([^/]+)/([^/]+)/(.*)', 'inginious.frontend.webapp.pages.tasks.TaskPageStaticDownload',
    r'/aggregation/([^/]+)', 'inginious.frontend.webapp.pages.aggregation.AggregationPage',
    r'/queue', 'inginious.frontend.webapp.pages.queue.QueuePage',
    r'/admin/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.utils.CourseRedirect',
    r'/admin/([^/]+)/settings', 'inginious.frontend.webapp.pages.course_admin.settings.CourseSettings',
    r'/admin/([^/]+)/students', 'inginious.frontend.webapp.pages.course_admin.student_list.CourseStudentListPage',
    r'/admin/([^/]+)/student/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.student_info.CourseStudentInfoPage',
    r'/admin/([^/]+)/student/([^/]+)/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.student_task.CourseStudentTaskPage',
    r'/admin/([^/]+)/student/([^/]+)/([^/]+)/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.submission.CourseStudentTaskSubmission',
    r'/admin/([^/]+)/aggregations', 'inginious.frontend.webapp.pages.course_admin.aggregation_list.CourseAggregationListPage',
    r'/admin/([^/]+)/aggregation/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.aggregation_info.CourseAggregationInfoPage',
    r'/admin/([^/]+)/aggregation/([^/]+)/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.aggregation_task.CourseAggregationTaskPage',
    r'/admin/([^/]+)/tasks', 'inginious.frontend.webapp.pages.course_admin.task_list.CourseTaskListPage',
    r'/admin/([^/]+)/task/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.task_info.CourseTaskInfoPage',
    r'/admin/([^/]+)/edit/aggregation/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.aggregation_edit.CourseEditAggregation',
    r'/admin/([^/]+)/edit/aggregations', 'inginious.frontend.webapp.pages.course_admin.aggregation_edit.CourseEditAggregation',
    r'/admin/([^/]+)/edit/task/([^/]+)', 'inginious.frontend.webapp.pages.course_admin.task_edit.CourseEditTask',
    r'/admin/([^/]+)/edit/task/([^/]+)/files', 'inginious.frontend.webapp.pages.course_admin.task_edit_file.CourseTaskFiles',
    r'/admin/([^/]+)/download', 'inginious.frontend.webapp.pages.course_admin.download.CourseDownloadSubmissions',
    r'/admin/([^/]+)/replay', 'inginious.frontend.webapp.pages.course_admin.replay.CourseReplaySubmissions',
    r'/admin/([^/]+)/danger', 'inginious.frontend.webapp.pages.course_admin.danger_zone.CourseDangerZonePage',
    r'/api/v0/auth_methods', 'inginious.frontend.webapp.pages.api.auth_methods.APIAuthMethods',
    r'/api/v0/authentication', 'inginious.frontend.webapp.pages.api.authentication.APIAuthentication',
    r'/api/v0/courses', 'inginious.frontend.webapp.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)', 'inginious.frontend.webapp.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks', 'inginious.frontend.webapp.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)', 'inginious.frontend.webapp.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions', 'inginious.frontend.webapp.pages.api.submissions.APISubmissions',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)',
        'inginious.frontend.webapp.pages.api.submissions.APISubmissionSingle',
)

urls_maintenance = (
    '/.*', 'inginious.frontend.webapp.pages.maintenance.MaintenancePage'
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


def _close_app(app, mongo_client, client):
    """ Ensures that the app is properly closed """
    app.stop()
    client.close()
    mongo_client.close()


def get_app(config):
    """
    :param config: the configuration dict
    :return: A new app
    """
    config = _put_configuration_defaults(config)

    appli = web.application((), globals(), autoreload=False)

    if config.get("maintenance", False):
        template_helper = TemplateHelper(PluginManager(), 'frontend/webapp/templates',
                                         'frontend/webapp/templates/layout',
                                         config.get('use_minified_js', True))
        template_helper.add_to_template_globals("get_homepath", lambda: web.ctx.homepath)
        appli.template_helper = template_helper
        appli.init_mapping(urls_maintenance)
        return appli.wsgifunc(), appli.stop

    task_directory = config["tasks_directory"]
    default_allowed_file_extensions = config['allowed_file_extensions']
    default_max_file_size = config['max_file_size']

    zmq_context, _ = start_asyncio_and_zmq()

    # Init the different parts of the app
    plugin_manager = PluginManager()

    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]
    gridfs = GridFS(database)

    course_factory, task_factory = create_factories(task_directory, plugin_manager, WebAppCourse, WebAppTask)

    user_manager = UserManager(web.session.Session(appli, MongoStore(database, 'sessions')), database, config.get('superadmins', []))

    update_pending_jobs(database)

    client = create_arch(config, task_directory, zmq_context)

    submission_manager = WebAppSubmissionManager(client, user_manager, database, gridfs, plugin_manager)

    template_helper = TemplateHelper(plugin_manager, 'frontend/webapp/templates', 'frontend/webapp/templates/layout',
                                     config.get('use_minified_js', True))

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
    template_helper.add_to_template_globals("get_homepath", lambda: web.ctx.homepath)
    template_helper.add_to_template_globals("user_manager", user_manager)
    template_helper.add_to_template_globals("default_allowed_file_extensions", default_allowed_file_extensions)
    template_helper.add_to_template_globals("default_max_file_size", default_max_file_size)
    template_helper.add_other("course_admin_menu",
                              lambda course, current: course_admin_utils.get_menu(course, current, template_helper.get_renderer(False),
                                                                                  plugin_manager, user_manager))

    # Not found page
    appli.notfound = lambda: web.notfound(template_helper.get_renderer().notfound('Page not found'))

    # Enable stacktrace display if logging is at level DEBUG
    if config.get('log_level', 'INFO') == 'DEBUG':
        appli.internalerror = debugerror

    # Insert the needed singletons into the application, to allow pages to call them
    appli.plugin_manager = plugin_manager
    appli.course_factory = course_factory
    appli.task_factory = task_factory
    appli.submission_manager = submission_manager
    appli.user_manager = user_manager
    appli.template_helper = template_helper
    appli.database = database
    appli.gridfs = gridfs
    appli.default_allowed_file_extensions = default_allowed_file_extensions
    appli.default_max_file_size = default_max_file_size
    appli.backup_dir = config.get("backup_directory", './backup')
    appli.webterm_link = config.get("webterm", None)

    # Init the mapping of the app
    appli.init_mapping(urls)

    # Loads plugins
    plugin_manager.load(client, appli, course_factory, task_factory, database, user_manager, submission_manager, config.get("plugins", []))

    # Start the inginious.backend
    client.start()

    return appli.wsgifunc(), lambda: _close_app(appli, mongo_client, client)
