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
""" Some utils for all the pages """


class INGIniousPage(object):
    """
    A base for all the pages of the INGInious webapp.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    def __init__(self, plugin_manager, course_factory, task_factory,submission_manager, batch_manager, user_manager, remote_ssh_manager,
                 template_helper, database, gridfs, default_allowed_file_extensions, default_max_file_size, containers):
        """
        Init the page
        :type plugin_manager: inginious.frontend.common.plugin_manager.PluginManager
        :type course_factory: inginious.common.course_factory.CourseFactory
        :type task_factory: inginious.common.task_factory.TaskFactory
        :type submission_manager: inginious.frontend.webapp.submission_manager.WebAppSubmissionManager
        :type batch_manager: inginious.frontend.webapp.batch_manager.BatchManager
        :type user_manager: inginious.frontend.webapp.user_manager.UserManager
        :type remote_ssh_manager: inginious.frontend.webapp.remote_ssh_manager.RemoteSSHManager
        :type template_helper: inginious.frontend.webapp.template_helper.TemplateHelper
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type default_allowed_file_extensions: list(str)
        :type default_max_file_size: int
        :type containers: list(str)
        """
        self.plugin_manager = plugin_manager
        self.course_factory = course_factory
        self.task_factory = task_factory
        self.submission_manager = submission_manager
        self.batch_manager = batch_manager
        self.user_manager = user_manager
        self.remote_ssh_manager = remote_ssh_manager
        self.template_helper = template_helper
        self.database = database
        self.gridfs = gridfs
        self.default_allowed_file_extensions = default_allowed_file_extensions
        self.default_max_file_size = default_max_file_size
        self.containers = containers
