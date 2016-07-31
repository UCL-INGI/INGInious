# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """


class INGIniousPage(object):
    """
    A base for all the pages of the INGInious webapp.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, batch_manager, user_manager,
                 template_helper, database, gridfs, default_allowed_file_extensions, default_max_file_size, backup_dir, containers):
        """
        Init the page
        :type plugin_manager: inginious.frontend.common.plugin_manager.PluginManager
        :type course_factory: inginious.common.course_factory.CourseFactory
        :type task_factory: inginious.common.task_factory.TaskFactory
        :type submission_manager: inginious.frontend.webapp.submission_manager.WebAppSubmissionManager
        :type batch_manager: inginious.frontend.webapp.batch_manager.BatchManager
        :type user_manager: inginious.frontend.webapp.user_manager.UserManager
        :type template_helper: inginious.frontend.webapp.template_helper.TemplateHelper
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type default_allowed_file_extensions: list(str)
        :type default_max_file_size: int
        :type backup_dir : str
        :type containers: list(str)
        """
        self.plugin_manager = plugin_manager
        self.course_factory = course_factory
        self.task_factory = task_factory
        self.submission_manager = submission_manager
        self.batch_manager = batch_manager
        self.user_manager = user_manager
        self.template_helper = template_helper
        self.database = database
        self.gridfs = gridfs
        self.default_allowed_file_extensions = default_allowed_file_extensions
        self.default_max_file_size = default_max_file_size
        self.backup_dir = backup_dir
        self.containers = containers
