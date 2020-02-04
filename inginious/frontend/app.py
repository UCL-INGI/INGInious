# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Starts the webapp """
import builtins
import pymongo

import inginious.frontend.pages.course_admin.utils as course_admin_utils
import web

from inginious.frontend.environment_types import register_base_env_types
from inginious.frontend.pages.internalerror import internalerror_generator

from gridfs import GridFS
from inginious.frontend.arch_helper import create_arch, start_asyncio_and_zmq
from inginious.frontend.cookieless_app import CookieLessCompatibleApplication
from inginious.frontend.courses import WebAppCourse
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.session_mongodb import MongoStore
from inginious.frontend.submission_manager import WebAppSubmissionManager
from inginious.frontend.submission_manager import update_pending_jobs
from inginious.frontend.tasks import WebAppTask
from inginious.frontend.template_helper import TemplateHelper
from inginious.frontend.user_manager import UserManager
from pymongo import MongoClient
from web.debugerror import debugerror, emailerrors

import inginious.frontend.pages.preferences.utils as preferences_utils
from inginious import get_root_path
from inginious.common.course_factory import create_factories
from inginious.common.entrypoints import filesystem_from_config_dict
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.lti_outcome_manager import LTIOutcomeManager

from inginious.frontend.task_problems import *

urls = (
    r'/?', 'inginious.frontend.pages.index.IndexPage',
    r'/index', 'inginious.frontend.pages.index.IndexPage',
    r'/courselist', 'inginious.frontend.pages.courselist.CourseListPage',
    r'/pages/([^/]+)', 'inginious.frontend.pages.utils.INGIniousStaticPage',
    r'/signin', 'inginious.frontend.pages.utils.SignInPage',
    r'/logout', 'inginious.frontend.pages.utils.LogOutPage',
    r'/register', 'inginious.frontend.pages.register.RegistrationPage',
    r'/auth/signin/([^/]+)', 'inginious.frontend.pages.social.AuthenticationPage',
    r'/auth/callback/([^/]+)', 'inginious.frontend.pages.social.CallbackPage',
    r'/auth/share/([^/]+)', 'inginious.frontend.pages.social.SharePage',
    r'/register/([^/]+)', 'inginious.frontend.pages.course_register.CourseRegisterPage',
    r'/course/([^/]+)', 'inginious.frontend.pages.course.CoursePage',
    r'/course/([^/]+)/([^/]+)', 'inginious.frontend.pages.tasks.TaskPage',
    r'/course/([^/]+)/([^/]+)/(.*)', 'inginious.frontend.pages.tasks.TaskPageStaticDownload',
    r'/group/([^/]+)', 'inginious.frontend.pages.group.GroupPage',
    r'/queue', 'inginious.frontend.pages.queue.QueuePage',
    r'/mycourses', 'inginious.frontend.pages.mycourses.MyCoursesPage',
    r'/preferences', 'inginious.frontend.pages.preferences.utils.RedirectPage',
    r'/preferences/profile', 'inginious.frontend.pages.preferences.profile.ProfilePage',
    r'/preferences/bindings', 'inginious.frontend.pages.preferences.bindings.BindingsPage',
    r'/preferences/delete', 'inginious.frontend.pages.preferences.delete.DeletePage',
    r'/admin/([^/]+)', 'inginious.frontend.pages.course_admin.utils.CourseRedirect',
    r'/admin/([^/]+)/settings', 'inginious.frontend.pages.course_admin.settings.CourseSettings',
    r'/admin/([^/]+)/students', 'inginious.frontend.pages.course_admin.student_list.CourseStudentListPage',
    r'/admin/([^/]+)/student/([^/]+)', 'inginious.frontend.pages.course_admin.student_info.CourseStudentInfoPage',
    r'/submission/([^/]+)', 'inginious.frontend.pages.course_admin.submission.SubmissionPage',
    r'/admin/([^/]+)/audiences', 'inginious.frontend.pages.course_admin.audience_list.CourseAudienceListPage',
    r'/admin/([^/]+)/submissions', 'inginious.frontend.pages.course_admin.submissions.CourseSubmissionsPage',
    r'/admin/([^/]+)/tasks', 'inginious.frontend.pages.course_admin.task_list.CourseTaskListPage',
    r'/admin/([^/]+)/tags', 'inginious.frontend.pages.course_admin.tags.CourseTagsPage',
    r'/admin/([^/]+)/groups', 'inginious.frontend.pages.course_admin.group_edit.CourseEditGroup',
    r'/admin/([^/]+)/edit/audience/([^/]+)', 'inginious.frontend.pages.course_admin.audience_edit.CourseEditAudience',
    r'/admin/([^/]+)/edit/task/([^/]+)', 'inginious.frontend.pages.course_admin.task_edit.CourseEditTask',
    r'/admin/([^/]+)/edit/task/([^/]+)/files', 'inginious.frontend.pages.course_admin.task_edit_file.CourseTaskFiles',
    r'/admin/([^/]+)/edit/task/([^/]+)/dd_upload', 'inginious.frontend.pages.course_admin.task_edit_file.CourseTaskFileUpload',
    r'/admin/([^/]+)/download', 'inginious.frontend.pages.course_admin.download.CourseDownloadSubmissions',
    r'/admin/([^/]+)/replay', 'inginious.frontend.pages.course_admin.replay.CourseReplaySubmissions',
    r'/admin/([^/]+)/danger', 'inginious.frontend.pages.course_admin.danger_zone.CourseDangerZonePage',
    r'/admin/([^/]+)/stats', 'inginious.frontend.pages.course_admin.statistics.CourseStatisticsPage',
    r'/admin/([^/]+)/stats/([^/]+)/([^/]+)', 'inginious.frontend.pages.course_admin.statistics.CourseStatisticsPage',
    r'/api/v0/auth_methods', 'inginious.frontend.pages.api.auth_methods.APIAuthMethods',
    r'/api/v0/authentication', 'inginious.frontend.pages.api.authentication.APIAuthentication',
    r'/api/v0/courses', 'inginious.frontend.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)', 'inginious.frontend.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks', 'inginious.frontend.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)', 'inginious.frontend.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions', 'inginious.frontend.pages.api.submissions.APISubmissions',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)',
        'inginious.frontend.pages.api.submissions.APISubmissionSingle',
    r'/lti/([^/]+)/([^/]+)', 'inginious.frontend.pages.lti.LTILaunchPage',
    r'/lti/bind', 'inginious.frontend.pages.lti.LTIBindPage',
    r'/lti/task', 'inginious.frontend.pages.lti.LTITaskPage',
    r'/lti/login', 'inginious.frontend.pages.lti.LTILoginPage',
    r'/lti/asset/(.*)', 'inginious.frontend.pages.lti.LTIAssetPage'
)

urls_maintenance = (
    '/.*', 'inginious.frontend.pages.maintenance.MaintenancePage'
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
    # First, disable debug. It will be enabled in the configuration, later.
    web.config.debug = False

    config = _put_configuration_defaults(config)

    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]
    gridfs = GridFS(database)

    # Init database if needed
    db_version = database.db_version.find_one({})
    if db_version is None:
        database.submissions.ensure_index([("username", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("submitted_on", pymongo.DESCENDING)])  # sort speed
        database.user_tasks.ensure_index(
            [("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)],
            unique=True)
        database.user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING)])
        database.user_tasks.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        database.user_tasks.ensure_index([("courseid", pymongo.ASCENDING)])
        database.user_tasks.ensure_index([("username", pymongo.ASCENDING)])

    appli = CookieLessCompatibleApplication(MongoStore(database, 'sessions'))

    # Init gettext
    available_translations = {
        "fr": "Français",
        "es": "Español",
        "pt": "Português",
        "el": "ελληνικά",
        "vi": "Tiếng Việt",
        "nl": "Nederlands",
        "de": "Deutsch"
    }

    available_languages = {"en": "English"}
    available_languages.update(available_translations)

    appli.add_translation("en", gettext.NullTranslations())  # English does not need translation ;-)
    for lang in available_translations.keys():
        appli.add_translation(lang, gettext.translation('messages', get_root_path() + '/frontend/i18n', [lang]))

    builtins.__dict__['_'] = appli.gettext

    if config.get("maintenance", False):
        template_helper = TemplateHelper(PluginManager(), None,
                                         'frontend/templates',
                                         'frontend/templates/layout',
                                         'frontend/templates/layout_lti',
                                         config.get('use_minified_js', True))
        template_helper.add_to_template_globals("get_homepath", appli.get_homepath)
        template_helper.add_to_template_globals("_", _)
        appli.template_helper = template_helper
        appli.init_mapping(urls_maintenance)
        return appli.wsgifunc(), appli.stop

    default_allowed_file_extensions = config['allowed_file_extensions']
    default_max_file_size = config['max_file_size']

    zmq_context, __ = start_asyncio_and_zmq(config.get('debug_asyncio', False))

    # Init the different parts of the app
    plugin_manager = PluginManager()

    # Add the "agent types" inside the frontend, to allow loading tasks and managing envs
    register_base_env_types(plugin_manager)

    # Create the FS provider
    if "fs" in config:
        fs_provider = filesystem_from_config_dict(config["fs"])
    else:
        task_directory = config["tasks_directory"]
        fs_provider = LocalFSProvider(task_directory)

    default_problem_types = {
        problem_type.get_type(): problem_type for problem_type in [DisplayableCodeProblem,
                                                                   DisplayableCodeSingleLineProblem,
                                                                   DisplayableFileProblem,
                                                                   DisplayableMultipleChoiceProblem,
                                                                   DisplayableMatchProblem]
    }

    course_factory, task_factory = create_factories(fs_provider, default_problem_types, plugin_manager, WebAppCourse, WebAppTask)

    user_manager = UserManager(appli.get_session(), database, config.get('superadmins', []))

    update_pending_jobs(database)

    client = create_arch(config, fs_provider, zmq_context, course_factory)

    lti_outcome_manager = LTIOutcomeManager(database, user_manager, course_factory)

    submission_manager = WebAppSubmissionManager(client, user_manager, database, gridfs, plugin_manager, lti_outcome_manager)

    template_helper = TemplateHelper(plugin_manager, user_manager, 'frontend/templates',
                                     'frontend/templates/layout',
                                     'frontend/templates/layout_lti',
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

    # Add some helpers for the templates
    template_helper.add_to_template_globals("_", _)
    template_helper.add_to_template_globals("str", str)
    template_helper.add_to_template_globals("available_languages", available_languages)
    template_helper.add_to_template_globals("get_homepath", appli.get_homepath)
    template_helper.add_to_template_globals("allow_registration", config.get("allow_registration", True))
    template_helper.add_to_template_globals("sentry_io_url", config.get("sentry_io_url"))
    template_helper.add_to_template_globals("user_manager", user_manager)
    template_helper.add_to_template_globals("default_allowed_file_extensions", default_allowed_file_extensions)
    template_helper.add_to_template_globals("default_max_file_size", default_max_file_size)
    template_helper.add_other("course_admin_menu",
                              lambda course, current: course_admin_utils.get_menu(course, current, template_helper.get_renderer(False),
                                                                                  plugin_manager, user_manager))
    template_helper.add_other("preferences_menu",
                              lambda current: preferences_utils.get_menu(appli, current, template_helper.get_renderer(False),
                                                                                 plugin_manager, user_manager))

    # Not found page
    appli.notfound = lambda: web.notfound(template_helper.get_renderer().notfound('Page not found'))

    # Enable stacktrace display if needed
    web_debug = config.get('web_debug', False)
    appli.internalerror = internalerror_generator(template_helper.get_renderer(False))
    if web_debug is True:
        web.config.debug = True
        appli.internalerror = debugerror
    elif isinstance(web_debug, str):
        web.config.debug = False
        appli.internalerror = emailerrors(web_debug, appli.internalerror)

    # Insert the needed singletons into the application, to allow pages to call them
    appli.plugin_manager = plugin_manager
    appli.course_factory = course_factory
    appli.task_factory = task_factory
    appli.submission_manager = submission_manager
    appli.user_manager = user_manager
    appli.template_helper = template_helper
    appli.database = database
    appli.gridfs = gridfs
    appli.client = client
    appli.default_allowed_file_extensions = default_allowed_file_extensions
    appli.default_max_file_size = default_max_file_size
    appli.backup_dir = config.get("backup_directory", './backup')
    appli.webterm_link = config.get("webterm", None)
    appli.lti_outcome_manager = lti_outcome_manager
    appli.allow_registration = config.get("allow_registration", True)
    appli.allow_deletion = config.get("allow_deletion", True)
    appli.available_languages = available_languages
    appli.welcome_page = config.get("welcome_page", None)
    appli.static_directory = config.get("static_directory", "./static")
    appli.webdav_host = config.get("webdav_host", None)

    # Init the mapping of the app
    appli.init_mapping(urls)

    # Loads plugins
    plugin_manager.load(client, appli, course_factory, task_factory, database, user_manager, submission_manager, config.get("plugins", []))

    # Start the inginious.backend
    client.start()

    return appli.wsgifunc(), lambda: _close_app(appli, mongo_client, client)
