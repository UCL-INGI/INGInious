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

from frontend import submission_manager
from frontend.plugins.plugin_manager import PluginManager
import common.base
import frontend.base
import frontend.session
urls = (
    '/', 'frontend.pages.index.IndexPage',
    '/index', 'frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'frontend.pages.tasks.TaskPage',
    '/admin/([^/]+)', 'frontend.pages.admin_course.AdminCourseTaskListPage',
    '/admin/([^/]+)/students', 'frontend.pages.admin_course.AdminCourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)', 'frontend.pages.admin_course.AdminCourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)', 'frontend.pages.admin_course.AdminCourseStudentTaskPage',
    '/admin/([^/]+)/tasks', 'frontend.pages.admin_course.AdminCourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)', 'frontend.pages.admin_course.AdminCourseTaskInfoPage',
    '/admin/([^/]+)/edit/([^/]+)', 'frontend.pages.admin_course_edit.AdminCourseEditTask',
)


def get_app(config_file):
    """ Get the application. config_file is the path to the JSON configuration file """
    appli = web.application(urls, globals(), autoreload=False)
    common.base.INGIniousConfiguration.load(config_file)

    frontend.base.init_database()
    frontend.session.init(appli)

    def not_found():
        """ Display the error 404 page """
        return web.notfound(frontend.base.renderer.notfound('Page not found'))
    appli.notfound = not_found

    submission_manager.init_backend_interface()

    # Must be done after everything else
    PluginManager(appli, common.base.INGIniousConfiguration.get("plugins", []))

    return appli

if __name__ == "__main__":
    app = get_app("./configuration.json")
    app.run()
