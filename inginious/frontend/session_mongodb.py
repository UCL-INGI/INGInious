# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#
# Copyright (c) Steven Anderson, Joshua Bronson
#
# Imported from https://github.com/whilefalse/webpy-mongodb-sessions/.
""" Saves sessions in the database """

from datetime import datetime
from typing import Pattern
from time import time

from bson.binary import Binary, USER_DEFINED_SUBTYPE
from web.session import Store

valid_key_types = {str}
atomic_types = {bool, int, float, str, bytes, type(None), Pattern, datetime}


def needs_encode(obj):
    '''
    >>> from re import compile
    >>> atomics = (True, 1, 1.0, '', None, compile(''), datetime.now(), b'')
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
    >>> needs_encode(b'1')
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
                   for (k, v) in obj.items())
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
        return dict((k, Binary(Store.encode(self, v), USER_DEFINED_SUBTYPE) if needs_encode(v) else v)
                    for (k, v) in sessiondict.items())

    def decode(self, sessiondict):
        return dict((k, Store.decode(self, v) if isinstance(v, Binary) and v.subtype == USER_DEFINED_SUBTYPE else v)
                    for (k, v) in sessiondict.items())

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
