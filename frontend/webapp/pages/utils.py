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

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, batch_manager, user_manager, template_helper, database,
                 gridfs, default_allowed_file_extensions, default_max_file_size, containers):
        """
        Init the page
        :type plugin_manager: frontend.common.plugin_manager.PluginManager
        :type course_factory: common.course_factory.CourseFactory
        :type task_factory: common.task_factory.TaskFactory
        :type submission_manager: frontend.webapp.submission_manager.WebAppSubmissionManager
        :type batch_manager: frontend.webapp.batch_manager.BatchManager
        :type user_manager: frontend.webapp.user_manager.UserManager
        :type template_helper: frontend.webapp.template_helper.TemplateHelper
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
        self.template_helper = template_helper
        self.database = database
        self.gridfs = gridfs
        self.default_allowed_file_extensions = default_allowed_file_extensions
        self.default_max_file_size = default_max_file_size
        self.containers = containers


def _webpy_fake_class_creator(inginious_page_cls, *args, **kwargs):
    """
    :param inginious_page_cls: path to a class inheriting from INGIniousPage, or directly the "class object"
    :param args: args to be sent to the constructor of the classes
    :param kwargs: kwargs to be sent to the constructor of the classes
    :return: a fake Class that proxies everything to an instance of the INGIniousPage
    """
    if isinstance(inginious_page_cls, basestring):
        mod, cls = inginious_page_cls.rsplit('.', 1)
        mod = __import__(mod, None, None, [''])
        cls = getattr(mod, cls)
    else:
        cls = inginious_page_cls

    obj = cls(*args, **kwargs)

    class WebPyFakeMetaClass(type):
        """
        A fake metaclass that proxies everything to an object
        """

        def __getattr__(cls, name):
            return getattr(obj.__class__, name)

    class WebPyFakeClass(object):
        """
        A fake class that proxies everything to an object
        """
        __metaclass__ = WebPyFakeMetaClass

        def __getattr__(self, name):
            return getattr(obj, name)

    return WebPyFakeClass


class WebPyFakeMapping(object):
    """
        A "fake" mapping class for web.py that init the classes it contains automatically. Allow to avoid global state
    """

    def __init__(self, urls, *args, **kwargs):
        """
        :param urls: Basic dict of pattern/classname pairs
        :param args: args to be sent to the constructor of the classes
        :param kwargs: kwargs to be sent to the constructor of the classes
        """
        self.dict = {}
        self.args = args
        self.kwargs = kwargs

        for pattern, classname in urls.iteritems():
            self.append((pattern, classname))

    def append(self, what):
        pattern, classname = what
        self.dict[pattern] = _webpy_fake_class_creator(classname, *self.args, **self.kwargs)

    def __iter__(self):
        return self.dict.iteritems().__iter__()
