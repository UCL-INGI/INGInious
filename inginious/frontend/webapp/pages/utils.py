# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some utils for all the pages """
from typing import List

import web
from gridfs import GridFS
from pymongo.database import Database

from common.course_factory import CourseFactory
from common.task_factory import TaskFactory
from frontend.common.plugin_manager import PluginManager
from frontend.common.submission_manager import SubmissionManager
from frontend.common.templates import TemplateHelper
from frontend.webapp.batch_manager import BatchManager
from frontend.webapp.user_manager import UserManager


class INGIniousPage(object):
    """
    A base for all the pages of the INGInious webapp.
    Contains references to the PluginManager, the CourseFactory, and the SubmissionManager
    """

    @property
    def app(self):
        return web.ctx.app_stack[0]

    @property
    def plugin_manager(self) -> PluginManager:
        return self.app.plugin_manager

    @property
    def course_factory(self) -> CourseFactory:
        return self.app.course_factory

    @property
    def task_factory(self) -> TaskFactory:
        return self.app.task_factory

    @property
    def submission_manager(self) -> SubmissionManager:
        return self.app.submission_manager

    @property
    def batch_manager(self) -> BatchManager:
        return self.app.batch_manager

    @property
    def user_manager(self) -> UserManager:
        return self.app.user_manager

    @property
    def template_helper(self) -> TemplateHelper:
        return self.app.template_helper

    @property
    def database(self) -> Database:
        return self.app.database

    @property
    def gridfs(self) -> GridFS:
        return self.app.gridfs

    @property
    def default_allowed_file_extensions(self) -> List[str]:
        return self.app.default_allowed_file_extensions

    @property
    def default_max_file_size(self) -> int:
        return self.app.default_max_file_size

    @property
    def backup_dir(self) -> str:
        return self.app.backup_dir

    @property
    def containers(self) -> List[str]:
        return self.app.submission_manager.get_available_environments()