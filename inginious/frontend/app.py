# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Starts the webapp """
import builtins
import os
import sys
from binascii import hexlify

import pymongo

import inginious.frontend.pages.course_admin.utils as course_admin_utils
import web
import flask

from inginious.frontend.environment_types import register_base_env_types
from inginious.frontend.pages.internalerror import internalerror_generator

from gridfs import GridFS
from inginious.frontend.arch_helper import create_arch, start_asyncio_and_zmq
from inginious.frontend.webpy.cookieless_app import CookieLessCompatibleApplication
from inginious.frontend.pages.utils import register_utils
from inginious.frontend.plugin_manager import PluginManager
from inginious.frontend.submission_manager import WebAppSubmissionManager
from inginious.frontend.submission_manager import update_pending_jobs
from inginious.frontend.template_helper import TemplateHelper
from inginious.frontend.user_manager import UserManager
from inginious.frontend.i18n_manager import I18nManager
from pymongo import MongoClient
from web.debugerror import debugerror, emailerrors

import inginious.frontend.pages.preferences.utils as preferences_utils
from inginious import get_root_path
from inginious.frontend.course_factory import create_factories
from inginious.common.entrypoints import filesystem_from_config_dict
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.lti_outcome_manager import LTIOutcomeManager

from inginious.frontend.task_problems import *
from inginious.frontend.task_dispensers.toc import TableOfContents
from inginious.frontend.task_dispensers.combinatory_test import CombinatoryTest

from inginious.frontend.app_dispatcher import AppDispatcher

from inginious.frontend.webpy.mapping import urls as webpy_mapping
from inginious.frontend.webpy.mapping import urls_maintenance
from inginious.frontend.webpy.mongo_sessions import MongoStore

from inginious.frontend.flask.mapping import init_flask_mapping
from inginious.frontend.flask.mongo_sessions import MongoDBSessionInterface

from werkzeug.exceptions import InternalServerError

def _put_configuration_defaults(config):
    """
    :param config: the basic configuration as a dict
    :return: the same dict, but with defaults for some unfilled parameters
    """
    if 'allowed_file_extensions' not in config:
        config['allowed_file_extensions'] = [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"]
    if 'max_file_size' not in config:
        config['max_file_size'] = 1024 * 1024

    if 'session_parameters' not in config or 'secret_key' not in config['session_parameters']:
        print("Please define a secret_key in the session_parameters part of the configuration.", file=sys.stderr)
        print("You can simply add the following (the text between the lines, without the lines) "
              "to your INGInious configuration file. We generated a random key for you.", file=sys.stderr)
        print("-------------", file=sys.stderr)
        print("session_parameters:", file=sys.stderr)
        print('\ttimeout: 86400  # 24 * 60 * 60, # 24 hours in seconds', file=sys.stderr)
        print('\tignore_change_ip: False # change this to True if you want user to keep their session if they change their IP', file=sys.stderr)
        print('\tsecure: False # change this to True if you only use https', file=sys.stderr)
        print('\tsecret_key: "{}"'.format(hexlify(os.urandom(32)).decode('utf-8')), file=sys.stderr)
        print("-------------", file=sys.stderr)
        exit(1)

    if 'session_parameters' not in config:
        config['session_parameters'] = {}
    default_session_parameters = {
        "cookie_name": "inginious_session_id",
        "cookie_domain": None,
        "cookie_path": None,
        "samesite": "Lax",
        "timeout": 86400,  # 24 * 60 * 60, # 24 hours in seconds
        "ignore_change_ip": False,
        "httponly": True,
        "secret_key": "fLjUfxqXtfNoIldA0A0G",
        "secure": False
    }
    for k, v in default_session_parameters.items():
        if k not in config['session_parameters']:
            config['session_parameters'][k] = v

    # flask migration
    config["SESSION_COOKIE_NAME"] = "inginious_session_id"
    config["SESSION_USE_SIGNER"] = True
    config["PERMANENT_SESSION_LIFETIME"] = config['session_parameters']["timeout"]
    config["SECRET_KEY"] = config['session_parameters']["secret_key"]

    return config


def get_homepath(ctx_homepath, session_func, ignore_session=False, force_cookieless=False):
    """
    :param ignore_session: Ignore the cookieless session_id that should be put in the URL
    :param force_cookieless: Force the cookieless session; the link will include the session_creator if needed.
    """
    session = session_func()
    if not ignore_session and session.get("session_id") is not None and session.get("cookieless", False):
        return ctx_homepath() + "/@" + session.get("session_id") + "@"
    elif not ignore_session and force_cookieless:
        return ctx_homepath() + "/@@"
    else:
        return ctx_homepath()


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

    web.config.session_parameters.update(config['session_parameters'])

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

    flask_app = flask.Flask(__name__)
    init_flask_mapping(flask_app)

    flask_app.config.from_mapping(**config)
    flask_app.session_interface = MongoDBSessionInterface(
        mongo_client, config.get('mongo_opt', {}).get('database', 'INGInious'),
        "sessions", config.get('SESSION_USE_SIGNER', False), True  # config.get('SESSION_PERMANENT', True)
    )

    webpy_app = CookieLessCompatibleApplication(MongoStore(database, 'sessions', web.config.session_parameters.timeout))
    appli = AppDispatcher(webpy_app.wsgifunc(), flask_app.wsgi_app)

    # TODO : These should be removed after flask migration
    session_func = lambda: webpy_app.get_session() if web.ctx.keys() else flask.session
    ctx_homepath = lambda: web.ctx.homepath if web.ctx.keys() else flask.request.url_root[:-1]
    appli_func = lambda: webpy_app if web.ctx.keys() else flask_app
    get_homepath_func = lambda ignore_session=False, force_cookieless=False: get_homepath(
        ctx_homepath, session_func, ignore_session, force_cookieless)

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

    i18n_manager = I18nManager(session_func)

    i18n_manager.translations["en"] = gettext.NullTranslations()  # English does not need translation ;-)
    for lang in available_translations.keys():
        i18n_manager.translations[lang] = gettext.translation('messages', get_root_path() + '/frontend/i18n', [lang])

    builtins.__dict__['_'] = i18n_manager.gettext

    if config.get("maintenance", False):
        template_helper = TemplateHelper(PluginManager(), None, config.get('use_minified_js', True))
        template_helper.add_to_template_globals("get_homepath", get_homepath_func)
        template_helper.add_to_template_globals("available_languages", available_languages)
        template_helper.add_to_template_globals("_", _)
        webpy_app.template_helper = template_helper
        webpy_app.init_mapping(urls_maintenance)
        return appli, webpy_app.stop

    default_allowed_file_extensions = config['allowed_file_extensions']
    default_max_file_size = config['max_file_size']

    zmq_context, __ = start_asyncio_and_zmq(config.get('debug_asyncio', False))

    # Init the different parts of the app
    plugin_manager = PluginManager()

    # Add the "agent types" inside the frontend, to allow loading tasks and managing envs
    register_base_env_types()

    # Create the FS provider
    if "fs" in config:
        fs_provider = filesystem_from_config_dict(config["fs"])
    else:
        task_directory = config["tasks_directory"]
        fs_provider = LocalFSProvider(task_directory)

    default_task_dispensers = {
        task_dispenser.get_id(): task_dispenser for task_dispenser in [TableOfContents, CombinatoryTest]
    }

    default_problem_types = {
        problem_type.get_type(): problem_type for problem_type in [DisplayableCodeProblem,
                                                                   DisplayableCodeSingleLineProblem,
                                                                   DisplayableFileProblem,
                                                                   DisplayableMultipleChoiceProblem,
                                                                   DisplayableMatchProblem]
    }

    course_factory, task_factory = create_factories(fs_provider, default_task_dispensers, default_problem_types, plugin_manager)

    user_manager = UserManager(session_func, database, config.get('superadmins', []))

    update_pending_jobs(database)

    client = create_arch(config, fs_provider, zmq_context, course_factory)

    lti_outcome_manager = LTIOutcomeManager(database, user_manager, course_factory)

    submission_manager = WebAppSubmissionManager(client, user_manager, database, gridfs, plugin_manager, lti_outcome_manager)

    template_helper = TemplateHelper(plugin_manager, user_manager, config.get('use_minified_js', True))

    register_utils(database, user_manager, template_helper)

    is_tos_defined = config.get("privacy_page", "") and config.get("terms_page", "")

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
    template_helper.add_to_template_globals("get_homepath", get_homepath_func)
    template_helper.add_to_template_globals("allow_registration", config.get("allow_registration", True))
    template_helper.add_to_template_globals("sentry_io_url", config.get("sentry_io_url"))
    template_helper.add_to_template_globals("user_manager", user_manager)
    template_helper.add_to_template_globals("default_allowed_file_extensions", default_allowed_file_extensions)
    template_helper.add_to_template_globals("default_max_file_size", default_max_file_size)
    template_helper.add_to_template_globals("is_tos_defined", is_tos_defined)
    template_helper.add_other("course_admin_menu",
                              lambda course, current: course_admin_utils.get_menu(course, current, template_helper.render,
                                                                                  plugin_manager, user_manager))
    template_helper.add_other("preferences_menu",
                              lambda current: preferences_utils.get_menu(appli_func, current, template_helper.render,
                                                                                 plugin_manager, user_manager))

    # Not found page
    def flask_not_found(e):
        return template_helper.render("notfound.html", message=e.description), 404
    flask_app.register_error_handler(404, flask_not_found)
    webpy_app.notfound = lambda message='Page not found': web.notfound(template_helper.render("notfound.html", message=message))

    # Forbidden page
    def flask_forbidden(e):
        return template_helper.render("forbidden.html", message=e.description), 403
    flask_app.register_error_handler(403, flask_forbidden)
    webpy_app.forbidden = lambda message='Forbidden': web.forbidden(template_helper.render("forbidden.html", message=message))

    # Enable stacktrace display if needed
    web_debug = config.get('web_debug', False)

    def flask_internalerror(e):
        return template_helper.render("internalerror.html", message=e.description), 500
    flask_app.register_error_handler(InternalServerError, flask_internalerror)

    webpy_app.internalerror = internalerror_generator(template_helper.render)
    if web_debug is True:
        web.config.debug = True
        flask_app.debug = True
        webpy_app.internalerror = debugerror
    elif isinstance(web_debug, str):
        web.config.debug = False
        flask_app.debug = False
        webpy_app.internalerror = emailerrors(web_debug, webpy_app.internalerror)

    # Insert the needed singletons into the application, to allow pages to call them
    for theapp in [webpy_app, flask_app]:
        theapp.plugin_manager = plugin_manager
        theapp.course_factory = course_factory
        theapp.task_factory = task_factory
        theapp.submission_manager = submission_manager
        theapp.user_manager = user_manager
        theapp.i18n_manager = i18n_manager
        theapp.template_helper = template_helper
        theapp.database = database
        theapp.gridfs = gridfs
        theapp.client = client
        theapp.default_allowed_file_extensions = default_allowed_file_extensions
        theapp.default_max_file_size = default_max_file_size
        theapp.backup_dir = config.get("backup_directory", './backup')
        theapp.webterm_link = config.get("webterm", None)
        theapp.lti_outcome_manager = lti_outcome_manager
        theapp.allow_registration = config.get("allow_registration", True)
        theapp.allow_deletion = config.get("allow_deletion", True)
        theapp.available_languages = available_languages
        theapp.welcome_page = config.get("welcome_page", None)
        theapp.terms_page = config.get("terms_page", None)
        theapp.privacy_page = config.get("privacy_page", None)
        theapp.static_directory = config.get("static_directory", "./static")
        theapp.webdav_host = config.get("webdav_host", None)

    # Init the mapping of the app
    webpy_app.init_mapping(webpy_mapping)

    # Loads plugins
    plugin_manager.load(client, appli_func, course_factory, task_factory, database, user_manager, submission_manager, config.get("plugins", []))

    # Start the inginious.backend
    client.start()

    return appli, lambda: _close_app(webpy_app, mongo_client, client)
