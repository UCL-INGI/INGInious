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
""" Contains helpers to send state to web.py pages """

class WebPyCustomMapping(object):
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
        if isinstance(classname, basestring):
            mod, cls = classname.rsplit('.', 1)
            mod = __import__(mod, None, None, [''])
            cls = getattr(mod, cls)
        else:
            cls = classname

        self.dict[pattern] = cls(*self.args, **self.kwargs)

    def __iter__(self):
        return self.dict.iteritems().__iter__()
