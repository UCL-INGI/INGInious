"""
Copyright (c) Gary Wilson Jr. <gary@thegarywilson.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


This module makes simple LDAP queries simple.
from https://github.com/gdub/python-simpleldap.

TODO remove this when PR for Py3 is accepted by devs of python-simpleldap.
"""

import ldap

class cidict(dict):
    """
    A re-implementation of the ldap module's cidict that inherits from dict instead
    of UserDict so that we can, in turn, inherit from cidict.

    Case-insensitive but case-respecting dictionary.
    """

    def __init__(self, default=None):
        self._keys = {}
        super(cidict, self).__init__({})
        self.update(default or {})

    def __getitem__(self, key):
        return super(cidict, self).__getitem__(key.lower())

    def __setitem__(self, key, value):
        lower_key = key.lower()
        self._keys[lower_key] = key
        super(cidict, self).__setitem__(lower_key, value)

    def __delitem__(self, key):
        lower_key = key.lower()
        del self._keys[lower_key]
        super(cidict, self).__delitem__(lower_key)

    def update(self, dict):
        for key in dict:
            self[key] = dict[key]

    def has_key(self, key):
        return super(cidict, self).__contains__(key.lower())

    __contains__ = has_key

    def get(self, key, *args, **kwargs):
        return super(cidict, self).get(key.lower(), *args, **kwargs)

    def keys(self):
        return self._keys.values()

    def items(self):
        return [(k, self[k]) for k in self.keys()]

#
# Exceptions.
#

class SimpleLDAPException(Exception):
    """Base class for all simpleldap exceptions."""


class ObjectNotFound(SimpleLDAPException):
    """
    Exception when no objects were returned, but was expecting a single item.
    """


class MultipleObjectsFound(SimpleLDAPException):
    """
    Exception for when multiple objects were returned, but was expecting only
    a single item.
    """


class ConnectionException(Exception):
    """Base class for all Connection object exceptions."""


class InvalidEncryptionProtocol(ConnectionException):
    """Exception when given an unsupported encryption protocol."""


#
# Classes.
#

class LDAPItem(cidict):
    """
    A convenience class for wrapping standard LDAPResult objects.
    """

    def __init__(self, result):
        super(LDAPItem, self).__init__()
        self.dn, self.attributes = result
        # XXX: quick and dirty, should really proxy straight to the existing
        # self.attributes dict.
        for attribute, values in self.attributes.items():
            # Make the entire list of values for each LDAP attribute
            # accessible through a dictionary mapping.
            self[attribute] = values

    def first(self, attribute):
        """
        Return the first value for the given LDAP attribute.
        """
        return self[attribute][0]

    def value_contains(self, value, attribute):
        """
        Determine if any of the items in the value list for the given
        attribute contain value.
        """
        for item in self[attribute]:
            if value in item:
                return True
        return False

    def __str__(self):
        """
        Print attribute names and values, one per line, in alphabetical order.

        Attribute names are displayed right-aligned to the length of the
        longest attribute name.
        """
        attributes = self.keys()
        longestKeyLength = max([len(attr) for attr in attributes])
        output = []
        for attr in sorted(attributes):
            values = ("\n%*s  " % (longestKeyLength, ' ')).join(self[attr])
            output.append("%*s: %s" % (longestKeyLength, attr, values))
        return "\n".join(output)

    def __eq__(self, other):
        return self.dn == other.dn


class Connection(object):
    """
    A connection to an LDAP server.
    """

    # The class to use for items returned in results.  Subclasses can change
    # this to a class of their liking.
    result_item_class = LDAPItem

    # List of exceptions to treat as a failed bind operation in the
    # authenticate method.
    failed_authentication_exceptions = [
        ldap.NO_SUCH_OBJECT,  # e.g. dn matches no objects.
        ldap.UNWILLING_TO_PERFORM,  # e.g. dn with no password.
        ldap.INVALID_CREDENTIALS,  # e.g. wrong password.
    ]

    def __init__(self, hostname='localhost', port=None, dn='', password='',
                 encryption=None, require_cert=None, debug=False,
                 initialize_kwargs=None, options=None, search_defaults=None):
        """
        Bind to hostname:port using the passed distinguished name (DN), as
        ``dn``, and password.

        If ``hostname`` is not given, default to ``'localhost'``.

        If no user and password is given, try to connect anonymously with a
        blank DN and password.

        ``encryption`` should be one of ``'tls'``, ``'ssl'``, or ``None``.
        If ``'tls'``, then the standard port 389 is used by default and after
        binding, tls is started.  If ``'ssl'``, then port 636 is used by
        default.  ``port`` can optionally be given for connecting to a
        non-default port.

        ``require_cert`` is None by default.  Set this to ``True`` or
        ``False`` to set the ``OPT_X_TLS_REQUIRE_CERT`` ldap option.

        If ``debug`` is ``True``, debug options are turned on within ldap and
        statements are ouput to standard error.  Default is ``False``.

        If given, ``options`` should be a dictionary of any additional
        connection-specific ldap  options to set, e.g.:
        ``{'OPT_TIMELIMIT': 3}``.

        If given, ``search_defaults`` should be a dictionary of default
        parameters to be passed to the search method.
        """
        if search_defaults is None:
            self._search_defaults = {}
        else:
            self._search_defaults = search_defaults

        if not encryption or encryption == 'tls':
            protocol = 'ldap'
            if not port:
                port = 389
        elif encryption == 'ssl':
            protocol = 'ldaps'
            if not port:
                port = 636
        else:
            raise InvalidEncryptionProtocol(
                "Invalid encryption protocol, must be one of: 'tls' or 'ssl'.")

        if require_cert is not None:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, require_cert)
        if debug:
            ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        else:
            ldap.set_option(ldap.OPT_DEBUG_LEVEL, 0)

        uri = '%s://%s:%s' % (protocol, hostname, port)
        if initialize_kwargs:
            self.connection = ldap.initialize(uri, **initialize_kwargs)
        else:
            self.connection = ldap.initialize(uri)
        if options:
            for name, value in options.items():
                self.connection.set_option(getattr(ldap, name), value)
        if encryption == 'tls':
            self.connection.start_tls_s()
        self.connection.simple_bind_s(dn, password)

    def set_search_defaults(self, **kwargs):
        """
        Set defaults for search.

        Examples::

            conn.set_search_defaults(base_dn='dc=example,dc=com', timeout=100)
            conn.set_search_defaults(attrs=['cn'], scope=ldap.SCOPE_BASE)
        """
        self._search_defaults.update(kwargs)

    def clear_search_defaults(self, args=None):
        """
        Clear all search defaults specified by the list of parameter names
        given as ``args``.  If ``args`` is not given, then clear all existing
        search defaults.

        Examples::

            conn.set_search_defaults(scope=ldap.SCOPE_BASE, attrs=['cn'])
            conn.clear_search_defaults(['scope'])
            conn.clear_search_defaults()
        """
        if args is None:
            self._search_defaults.clear()
        else:
            for arg in args:
                if arg in self._search_defaults:
                    del self._search_defaults[arg]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """
        Shutdown the connection.
        """
        self.connection.unbind_s()

    def search(self, filter, base_dn=None, attrs=None, scope=None,
               timeout=None, limit=None):
        """
        Search the directory.
        """
        if base_dn is None:
            base_dn = self._search_defaults.get('base_dn', '')
        if attrs is None:
            attrs = self._search_defaults.get('attrs', None)
        if scope is None:
            scope = self._search_defaults.get('scope', ldap.SCOPE_SUBTREE)
        if timeout is None:
            timeout = self._search_defaults.get('timeout', -1)
        if limit is None:
            limit = self._search_defaults.get('limit', 0)

        results = self.connection.search_ext_s(
            base_dn, scope, filter, attrs, timeout=timeout, sizelimit=limit)
        return self.to_items(results)

    def get(self, *args, **kwargs):
        """
        Get a single object.

        This is a convenience wrapper for the search method that checks that
        only one object was returned, and returns that single object instead
        of a list.  This method takes the exact same arguments as search.
        """
        results = self.search(*args, **kwargs)
        num_results = len(results)
        if num_results == 1:
            return results[0]
        if num_results > 1:
            raise MultipleObjectsFound()
        raise ObjectNotFound()

    def to_items(self, results):
        """
        Turn LDAPResult objects returned from the ldap library into more
        convenient objects.
        """
        return [self.result_item_class(item) for item in results]

    def authenticate(self, dn='', password=''):
        """
        Attempt to authenticate given dn and password using a bind operation.
        Return True if the bind is successful, and return False there was an
        exception raised that is contained in
        self.failed_authentication_exceptions.
        """
        try:
            self.connection.simple_bind_s(dn, password)
        except tuple(self.failed_authentication_exceptions):
            return False
        else:
            return True

    def compare(self, dn, attr, value):
        """
        Compare the ``attr`` of the entry ``dn`` with given ``value``.

        This is a convenience wrapper for the ldap library's ``compare``
        function that returns a boolean value instead of 1 or 0.
        """
        return self.connection.compare_s(dn, attr, value) == 1
