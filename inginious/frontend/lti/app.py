# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Starts the webapp """
import logging

from gridfs import GridFS
from pymongo import MongoClient
import pymongo
import web

from inginious.frontend.common.arch_helper import create_arch, start_asyncio_and_zmq
from inginious.frontend.common.session_mongodb import MongoStore
from inginious.frontend.common.plugin_manager import PluginManager
from inginious.common.course_factory import create_factories
from inginious.frontend.common.tasks import FrontendTask
from inginious.frontend.common.courses import FrontendCourse
from inginious.frontend.common.template_helper import TemplateHelper
from inginious.frontend.lti.lis_outcome_manager import LisOutcomeManager
from inginious.frontend.lti.submission_manager import LTISubmissionManager
from inginious.frontend.lti.user_manager import UserManager
from inginious.frontend.lti.custom_session import CustomSession
from inginious.frontend.common.submission_manager import update_pending_jobs

urls = (
    r"/launch/([a-zA-Z0-9\-_]+)/([a-zA-Z0-9\-_]+)", "inginious.frontend.lti.pages.launch.LTILaunchTask",
    r"/([a-zA-Z0-9\-_]+)/task", "inginious.frontend.lti.pages.task.LTITask",
    r"/([a-zA-Z0-9\-_]+)/download", "inginious.frontend.lti.pages.download.LTIDownload",
    r'/([a-zA-Z0-9\-_]+)/([^/]+)/(.*)', 'inginious.frontend.lti.pages.task.LTITaskPageStaticDownload'
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


def _close_app(app, mongo_client, client, lis_outcome_manager):
    """ Ensures that the app is properly closed """
    app.stop()
    lis_outcome_manager.stop()
    client.close()
    mongo_client.close()


def update_database(database):
    """
    Checks the database version and update the db if necessary
    """

    logger = logging.getLogger("inginious.db_update")

    db_version = database.db_version.find_one({})
    if db_version is None:
        db_version = 0
    else:
        db_version = db_version['db_version']

    if db_version < 1:
        logger.info("Updating database to db_version 1")
        # Init the database
        database.submissions.ensure_index([("username", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("submitted_on", pymongo.DESCENDING)])  # sort speed
        db_version = 1

    database.db_version.update({}, {"$set": {"db_version": db_version}}, upsert=True)


def get_app(config):
    """
    :param config: the configuration dict
    :param active_callback: a callback without arguments that will be called when the app is fully initialized
    :return: A new app
    """
    config = _put_configuration_defaults(config)

    task_directory = config["tasks_directory"]
    download_directory = config.get("download_directory", "lti_download")
    default_allowed_file_extensions = config['allowed_file_extensions']
    default_max_file_size = config['max_file_size']

    appli = web.application((), globals(), autoreload=False)

    zmq_context, _ = start_asyncio_and_zmq()

    # Init the different parts of the app
    plugin_manager = PluginManager()

    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]
    gridfs = GridFS(database)

    course_factory, task_factory = create_factories(task_directory, plugin_manager, FrontendCourse, FrontendTask)

    #
    # Allow user config to over-rider the username strong in Mongo.
    # This is enabled by most LMS's such as Moodle, and the ext_user_username
    # is the "login name" for the user, which is typically the same as
    # would be authenticated by logging into the course via ldap
    #
    lti_user_name = config.get('lti_user_name', 'user_id')
    if lti_user_name not in ['user_id', 'ext_user_username'] :
        lti_user_name = 'user_id'

    user_manager = UserManager(CustomSession(appli, MongoStore(database, 'sessions')), database, lti_user_name)

    update_pending_jobs(database)

    client = create_arch(config, task_directory, zmq_context)

    lis_outcome_manager = LisOutcomeManager(database, user_manager, course_factory, config["lti"])

    submission_manager = LTISubmissionManager(client, user_manager, database, gridfs, plugin_manager,
                                              config.get('nb_submissions_kept', 5), lis_outcome_manager)

    template_helper = TemplateHelper(plugin_manager, 'frontend/lti/templates', 'frontend/lti/templates/layout', config.get('use_minified_js', True))

    # Update the database
    update_database(database)

    # Add some helpers for the templates
    template_helper.add_to_template_globals("get_homepath", lambda: web.ctx.homepath)
    template_helper.add_to_template_globals("user_manager", user_manager)
    template_helper.add_to_template_globals("default_allowed_file_extensions", default_allowed_file_extensions)
    template_helper.add_to_template_globals("default_max_file_size", default_max_file_size)

    # Not found page
    appli.notfound = lambda: web.notfound(template_helper.get_renderer().notfound('Page not found'))

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
    appli.consumers = config["lti"]
    appli.download_directory = download_directory
    appli.download_status = {}
    appli.webterm_link = config.get("webterm", None)

    # Init the mapping of the app
    appli.init_mapping(urls)

    # Loads plugins
    plugin_manager.load(client, appli, course_factory, task_factory, database, user_manager, submission_manager, config.get("plugins", []))

    # Start the Client
    client.start()

    return appli.wsgifunc(), lambda: _close_app(appli, mongo_client, client, lis_outcome_manager)
