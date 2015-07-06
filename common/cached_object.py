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
""" An helper class that automagically caches objects that have a dependence on the disk """

import os
from abc import abstractmethod


class _CachedClassMeta(type):
    """ A hidden metaclass that "singletonize" all cached objects """

    __object_cache = {}
    __cache_hits = 0
    __cache_miss = 0

    def __call__(cls, *args, **kwargs):
        """ :type cls: CachedClass && _CachedClassMeta """
        # Get the cache key; if it is None, simply create a new object
        cache_key = cls._get_cache_key(*args, **kwargs)
        if cache_key is None:
            return super(_CachedClassMeta, cls).__call__(*args, **kwargs)

        # If it is not yet in the cache, create the object and put it in the cache
        obj_cache = cls.__get_obj_cache()
        if cache_key not in obj_cache:
            obj_cache[cache_key] = cls.__create_cache(*args, **kwargs)
            _CachedClassMeta.__cache_miss += 1
        elif cls.__cache_needs_update(obj_cache[cache_key]):
            obj_cache[cache_key] = cls.__update_cache(obj_cache[cache_key])
            _CachedClassMeta.__cache_miss += 1
        else:
            _CachedClassMeta.__cache_hits += 1

        #print "Cache stats: ({}, {})".format(_CachedClassMeta.__cache_hits, _CachedClassMeta.__cache_miss)

        return obj_cache[cache_key][0]

    def __create_cache(cls, *args, **kwargs):
        """ Helper to create a new tuple for the cache """
        obj = super(_CachedClassMeta, cls).__call__(*args, **kwargs)
        file_path = obj._file_cache_check()
        return (obj, os.stat(file_path).st_mtime)

    def __cache_needs_update(cls, cache_tuple):
        """ Check if the cache needs to be updated """
        file_path = cache_tuple[0]._file_cache_check()
        return os.stat(file_path).st_mtime != cache_tuple[1]

    def __update_cache(cls, cache_tuple):
        """ Update the cache tuple"""
        file_path = cache_tuple[0]._file_cache_check()
        cache_tuple[0].reload()
        return (cache_tuple[0], os.stat(file_path).st_mtime)

    def __get_obj_cache(cls):
        if cls not in _CachedClassMeta.__object_cache:
            _CachedClassMeta.__object_cache[cls] = {}
        return _CachedClassMeta.__object_cache[cls]

class CachedClass(object):

    __metaclass__ = _CachedClassMeta

    @classmethod
    def _get_cache_key(cls, *args, **kwargs):
        """
            Returns a key to be used to cache an object. *args and **kwargs are the ones passed to the normal constructor.
            Returning None make the current object not being cached.
            This probably needs to be overriden
        """
        return (args, kwargs)  # bad idea most of the time

    @abstractmethod
    def _file_cache_check(self):
        """ Returns the path to check for updates """
        pass

    @abstractmethod
    def reload(self):
        """ Reloads the object from disk """
        pass