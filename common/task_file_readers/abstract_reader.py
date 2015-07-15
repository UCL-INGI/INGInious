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
""" Task file managers """
from abc import ABCMeta, abstractmethod


class AbstractTaskFileReader(object):
    """ Manages a type of task file """
    __metaclass__ = ABCMeta

    @abstractmethod
    def load(self, file_content):
        """ Parses file_content and returns a dict describing a task """
        pass

    @abstractmethod
    def get_ext(self):
        """ Returns the task file extension. Must be @classmethod! """
        pass

    @abstractmethod
    def dump(self, descriptor):
        """ Dump descriptor and returns the content that should be written to the task file"""
        pass
