#!/usr/bin/env python
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
""" Starts the frontend """

import web

import common.base
from frontend import submission_manager
import frontend.base
from frontend.database_updater import update_database
from frontend.plugins.plugin_manager import PluginManager
import frontend.session
from frontend.template_helper import TemplateHelper
urls = (
    '/', 'frontend.pages.index.IndexPage',
    '/index', 'frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'frontend.pages.tasks.TaskPage',
    '/course/([^/]+)/([^/]+)/(.*)', 'frontend.pages.tasks.TaskPageStaticDownload',
    '/admin/([^/]+)', 'frontend.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/settings', 'frontend.pages.course_admin.settings.CourseSettings',
    '/admin/([^/]+)/students', 'frontend.pages.course_admin.student_list.CourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)', 'frontend.pages.course_admin.student_info.CourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)', 'frontend.pages.course_admin.student_task.CourseStudentTaskPage',
    '/admin/([^/]+)/tasks', 'frontend.pages.course_admin.task_list.CourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)', 'frontend.pages.course_admin.task_info.CourseTaskInfoPage',
    '/admin/([^/]+)/edit/([^/]+)', 'frontend.pages.course_admin.task_edit.CourseEditTask',
    '/admin/([^/]+)/files/([^/]+)', 'frontend.pages.course_admin.task_file.DownloadTaskFiles',
    '/admin/([^/]+)/submissions', 'frontend.pages.course_admin.submission_files.DownloadSubmissionFiles'
)


def get_app(config_file):
    """ Get the application. config_file is the path to the JSON configuration file """
    appli = web.application(urls, globals(), autoreload=False)
    common.base.INGIniousConfiguration.load(config_file)

    frontend.base.init_database()
    update_database()
    frontend.session.init(appli)

    def not_found():
        """ Display the error 404 page """
        return web.notfound(frontend.base.renderer.notfound('Page not found'))
    appli.notfound = not_found

    plugin_manager = PluginManager(appli, common.base.INGIniousConfiguration.get("plugins", []))

    # Plugin Manager is also a Hook Manager
    submission_manager.init_backend_interface(plugin_manager)

    # Loads template_helper
    TemplateHelper()

    # Loads plugins
    plugin_manager.load()

    return appli

if __name__ == "__main__":
    app = get_app("./configuration.json")
    app.run()
