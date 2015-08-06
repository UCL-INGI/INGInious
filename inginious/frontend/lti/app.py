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

import os
import signal
import threading

from gridfs import GridFS
from pymongo import MongoClient
import pymongo
import web

from inginious.backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from inginious.frontend.common import backend_interface
from inginious.frontend.common.session_mongodb import MongoStore
from inginious.frontend.common.static_middleware import StaticMiddleware
from inginious.frontend.common.plugin_manager import PluginManager
from inginious.common.course_factory import create_factories
from inginious.frontend.common.tasks import FrontendTask
from inginious.frontend.common.courses import FrontendCourse
from inginious.frontend.common.templates import TemplateHelper
from inginious.frontend.common.webpy_fake_mapping import WebPyFakeMapping
from inginious.frontend.lti.lis_outcome_manager import LisOutcomeManager
from inginious.frontend.lti.submission_manager import LTISubmissionManager
from inginious.frontend.lti.user_manager import UserManager

urls = {
    r"/launch/([a-zA-Z0-9\-_]+)/([a-zA-Z0-9\-_]+)": "frontend.lti.pages.launch.LTILaunchTask",
    r"/([a-zA-Z0-9\-_]+)/task": "frontend.lti.pages.task.LTITask"
}

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


def _close_app(app, mongo_client, job_manager, lis_outcome_manager):
    """ Ensures that the app is properly closed """
    app.stop()
    lis_outcome_manager.stop()
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
    # start_mutex = threading.Lock()
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


def update_database(database):
    """
    Checks the database version and update the db if necessary
    """

    db_version = database.db_version.find_one({})
    if db_version is None:
        db_version = 0
    else:
        db_version = db_version['db_version']

    if db_version < 1:
        print "Updating database to db_version 1"
        # Init the database
        database.submissions.ensure_index([("username", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("submitted_on", pymongo.DESCENDING)])  # sort speed
        db_version = 1

    database.db_version.update({}, {"$set": {"db_version": db_version}}, upsert=True)


def get_app(config, active_callback=None):
    """
    :param config: the configuration dict
    :param active_callback: a callback without arguments that will be called when the app is fully initialized
    :return: A new app
    """
    config = _put_configuration_defaults(config)

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

    user_manager = UserManager(web.session.Session(appli, MongoStore(database, 'sessions')), database)

    backend_interface.update_pending_jobs(database)

    job_manager = backend_interface.create_job_manager(config, plugin_manager,
                                                       task_directory, course_factory, task_factory)

    lis_outcome_manager = LisOutcomeManager(database, user_manager, course_factory, config["lti"])

    submission_manager = LTISubmissionManager(job_manager, user_manager, database, gridfs, plugin_manager,
                                              config.get('nb_submissions_kept', 5), lis_outcome_manager)

    template_helper = TemplateHelper(plugin_manager, 'frontend/lti/templates', 'layout', config.get('use_minified_js', True))

    # Update the database
    update_database(database)

    # Add some helpers for the templates
    template_helper.add_to_template_globals("user_manager", user_manager)
    template_helper.add_to_template_globals("default_allowed_file_extensions", default_allowed_file_extensions)
    template_helper.add_to_template_globals("default_max_file_size", default_max_file_size)

    # Not found page
    appli.notfound = lambda: web.notfound(template_helper.get_renderer().notfound('Page not found'))

    # Init the mapping of the app
    appli.mapping = WebPyFakeMapping(dict(urls), plugin_manager,
                                     course_factory, task_factory,
                                     submission_manager, user_manager,
                                     template_helper, database, gridfs,
                                     default_allowed_file_extensions, default_max_file_size,
                                     config["containers"].keys(),
                                     config["lti"])

    # Active hook
    if active_callback is not None:
        _handle_active_hook(job_manager, plugin_manager, active_callback)

    # Loads plugins
    plugin_manager.load(job_manager, appli, course_factory, task_factory, user_manager, config.get("plugins", []))

    # Start the inginious.backend
    job_manager.start()

    return appli, lambda: _close_app(appli, mongo_client, job_manager, lis_outcome_manager)


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

    inginious_root_path = os.path.relpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')), os.getcwd())
    func = StaticMiddleware(func, (
        ('/static/common/', os.path.join(inginious_root_path, 'frontend/common/static')),
        ('/static/lti/', os.path.join(inginious_root_path, 'frontend/lti/static'))
    ))

    func = web.httpserver.LogMiddleware(func)
    server = web.httpserver.WSGIServer((hostname, port), func)
    print "http://%s:%d/" % (hostname, port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
