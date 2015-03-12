#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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

import web
import os

import inginious
import inginious.common.base
from inginious.frontend import submission_manager
import inginious.frontend.base
from inginious.frontend.database_updater import update_database
from inginious.frontend.plugins.plugin_manager import PluginManager
import inginious.frontend.session
from inginious.frontend.template_helper import TemplateHelper
urls = (
    '/', 'inginious.frontend.pages.index.IndexPage',
    '/index', 'inginious.frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'inginious.frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'inginious.frontend.pages.tasks.TaskPage',
    '/course/([^/]+)/([^/]+)/(.*)', 'inginious.frontend.pages.tasks.TaskPageStaticDownload',
    '/admin/([^/]+)', 'inginious.frontend.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/settings', 'inginious.frontend.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/students', 'inginious.frontend.pages.course_admin.student_list.CourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)', 'inginious.frontend.pages.course_admin.student_info.CourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)', 'inginious.frontend.pages.course_admin.student_task.CourseStudentTaskPage',
    '/admin/([^/]+)/tasks', 'inginious.frontend.pages.course_admin.task_list.CourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)', 'inginious.frontend.pages.course_admin.task_info.CourseTaskInfoPage',
    '/admin/([^/]+)/edit/([^/]+)', 'inginious.frontend.pages.course_admin.task_edit.CourseEditTask',
    '/admin/([^/]+)/files/([^/]+)', 'inginious.frontend.pages.course_admin.task_file.DownloadTaskFiles',
    '/admin/([^/]+)/submissions', 'inginious.frontend.pages.course_admin.submission_files.DownloadSubmissionFiles'
)


def get_app(config_file):
    """ Get the application. config_file is the path to the JSON configuration file """
    appli = web.application(urls, globals(), autoreload=False)
    inginious.common.base.INGIniousConfiguration.load(config_file)

    inginious.frontend.base.init_database()
    update_database()
    inginious.frontend.session.init(appli)

    def not_found():
        """ Display the error 404 page """
        return web.notfound(inginious.frontend.base.renderer.notfound('Page not found'))
    appli.notfound = not_found

    plugin_manager = PluginManager(appli, inginious.common.base.INGIniousConfiguration.get("plugins", []))

    # Plugin Manager is also a Hook Manager
    submission_manager.init_backend_interface(plugin_manager)

    # Loads template_helper
    TemplateHelper()

    # Loads plugins
    plugin_manager.load()

    return appli

def get_config():
    for filename in [
            # search in the following locations (freely inspired from ansible):
            # * INGINIOUS_CONFIG (an environment variable)
            # * configuration.json (in the current directory)
            # * .inginious.json (in the home directory)
            # * /etc/inginious/configuration.json

            os.environ.get("INGINIOUS_CONF", ""),
            os.path.join(os.curdir, "configuration.json"),
            os.path.join(os.path.expanduser("~"), ".inginious.json"),
            "/etc/inginious/configuration.json",
        ]:
            if os.path.exists(filename):
                return filename
    raise "Cannot find configuration.json !"

if __name__ == "__main__":
    app = get_app(get_config())
    os.chdir(os.path.dirname(inginious.__file__))
    app.run()
