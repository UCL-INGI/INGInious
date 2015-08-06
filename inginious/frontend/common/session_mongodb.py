# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
# Copyright (c) Steven Anderson, Joshua Bronson
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
#
# Imported from https://github.com/whilefalse/webpy-mongodb-sessions/.
""" Saves sessions in the database """

from datetime import datetime
from re import _pattern_type
from time import time

from bson.binary import Binary
from web.session import Store

valid_key_types = set((str, unicode))
atomic_types = set((bool, int, long, float, str, unicode, type(None),
                    _pattern_type, datetime))


def needs_encode(obj):
    '''
    >>> from re import compile
    >>> atomics = (True, 1, 1L, 1.0, '', u'', None, compile(''), datetime.now())
    >>> any(needs_encode(i) for i in atomics)
    False
    >>> needs_encode([1, 2, 3])
    False
    >>> needs_encode([])
    False
    >>> needs_encode([1, [2, 3]])
    False
    >>> needs_encode({})
    False
    >>> needs_encode({'1': {'2': 3}})
    False
    >>> needs_encode({'1': [2]})
    False

    Objects that don't round trip need encoding::

    >>> needs_encode(tuple())
    True
    >>> needs_encode(set())
    True
    >>> needs_encode([1, [set()]])
    True
    >>> needs_encode({'1': {'2': set()}})
    True

    Mongo rejects dicts with non-string keys so they need encoding too::

    >>> needs_encode({1: 2})
    True
    >>> needs_encode({'1': {None: True}})
    True
    '''
    obtype = type(obj)
    if obtype in atomic_types:
        return False
    if obtype is list:
        return any(needs_encode(i) for i in obj)
    if obtype is dict:
        return any(type(k) not in valid_key_types or needs_encode(v)
                   for (k, v) in obj.iteritems())
    return True


#: field name used for id
_id = '_id'
#: field name used for accessed time
_atime = 'atime'
#: field name used for data
_data = 'data'


class MongoStore(Store):
    """ Allow to store web.py sessions in MongoDB """

    def __init__(self, database, collection_name='sessions'):
        self.collection = database[collection_name]
        self.collection.ensure_index(_atime)

    def encode(self, sessiondict):
        return dict((k, Binary(Store.encode(self, v)) if needs_encode(v) else v)
                    for (k, v) in sessiondict.iteritems())

    def decode(self, sessiondict):
        return dict((k, Store.decode(self, v) if isinstance(v, Binary) else v)
                    for (k, v) in sessiondict.iteritems())

    def __contains__(self, sessionid):
        return bool(self.collection.find_one({_id: sessionid}))

    def __getitem__(self, sessionid):
        sess = self.collection.find_one({_id: sessionid})
        if not sess:
            raise KeyError(sessionid)
        self.collection.update({_id: sessionid}, {'$set': {_atime: time()}})
        return self.decode(sess[_data])

    def __setitem__(self, sessionid, sessiondict):
        data = self.encode(sessiondict)
        self.collection.save({_id: sessionid, _data: data, _atime: time()})

    def __delitem__(self, sessionid):
        self.collection.remove({_id: sessionid})

    def cleanup(self, timeout):
        '''
        Removes all sessions older than ``timeout`` seconds.
        Called automatically on every session access.
        '''
        cutoff = time() - timeout
        self.collection.remove({_atime: {'$lt': cutoff}})


if __name__ == '__main__':
    import doctest

    doctest.testmod(optionflags=doctest.ELLIPSIS)
