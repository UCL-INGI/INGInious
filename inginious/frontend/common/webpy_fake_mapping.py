# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

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
