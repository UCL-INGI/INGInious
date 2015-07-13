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

    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, batch_manager):
        self.plugin_manager = plugin_manager
        self.course_factory = course_factory
        self.task_factory = task_factory
        self.submission_manager = submission_manager
        self.batch_manager = batch_manager


def _webpy_fake_class_creator(inginious_page_cls, plugin_manager, course_factory, task_factory, submission_manager, batch_manager):
    """
    :param inginious_page_cls: path to a class inheriting from INGIniousPage, or directly the "class object"
    :param plugin_manager:
    :param course_factory:
    :param task_factory:
    :param submission_manager:
    :param batch_manager:
    :return: a fake Class that proxies everything to an instance of the INGIniousPage
    """
    if isinstance(inginious_page_cls, basestring):
        mod, cls = inginious_page_cls.rsplit('.', 1)
        mod = __import__(mod, None, None, [''])
        cls = getattr(mod, cls)
    else:
        cls = inginious_page_cls

    obj = cls(plugin_manager, course_factory, task_factory, submission_manager, batch_manager)

    class WebPyFakeMetaClass(type):
        """
        A fake metaclass that proxies everything to an object
        """

        def __getattr__(cls, name):
            return getattr(obj.__class__,name)

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
    def __init__(self, plugin_manager, course_factory, task_factory, submission_manager, batch_manager, urls):
        self.dict = {}
        self.plugin_manager = plugin_manager
        self.course_factory = course_factory
        self.task_factory = task_factory
        self.submission_manager = submission_manager
        self.batch_manager = batch_manager

        for pattern, classname in urls.iteritems():
            self.append((pattern, classname))

    def append(self, what):
        pattern, classname = what
        self.dict[pattern] = _webpy_fake_class_creator(classname, self.plugin_manager, self.course_factory,
                                                       self.task_factory, self.submission_manager, self.batch_manager)

    def __iter__(self):
        return self.dict.iteritems().__iter__()