# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Contains AccessibleTime, class that represents the period of time when a course/task is accessible """

from datetime import datetime


def parse_date(date, default=None):
    """ Parse a valid date """
    if date == "":
        if default is not None:
            return default
        else:
            raise Exception("Unknown format for " + date)

    for format_type in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y %H",
                        "%d/%m/%Y"]:
        try:
            return datetime.strptime(date, format_type)
        except ValueError:
            pass
    raise Exception("Unknown format for " + date)


class AccessibleTime(object):
    """ represents the period of time when a course/task is accessible """

    def __init__(self, val=None):
        """
            Parse a string/a boolean to get the correct time period.
            Correct values for val:
            True (task always open)
            False (task always closed)
            2014-07-16 11:24:00 (task is open from 2014-07-16 at 11:24:00)
            2014-07-16 (task is open from 2014-07-16)
            / 2014-07-16 11:24:00 (task is only open before the 2014-07-16 at 11:24:00)
            / 2014-07-16 (task is only open before the 2014-07-16)
            2014-07-16 11:24:00 / 2014-07-20 11:24:00 (task is open from 2014-07-16 11:24:00 and will be closed the 2014-07-20 at 11:24:00)
            2014-07-16 / 2014-07-20 11:24:00 (...)
            2014-07-16 11:24:00 / 2014-07-20 (...)
            2014-07-16 / 2014-07-20 (...)
        """
        if val is None or val == "" or val is True:
            self._val = [datetime.min, datetime.max]
        elif val == False:
            self._val = [datetime.max, datetime.max]
        else:  # str
            values = val.split("/")
            if len(values) == 1:
                self._val = [parse_date(values[0].strip(), datetime.min), datetime.max]
            else:
                self._val = [parse_date(values[0].strip(), datetime.min), parse_date(values[1].strip(), datetime.max)]

    def before_start(self, when=None):
        """ Returns True if the task/course is not yet accessible """
        if when is None:
            when = datetime.now()

        return self._val[0] > when

    def after_start(self, when=None):
        """ Returns True if the task/course is or have been accessible in the past """
        return not self.before_start(when)

    def is_open(self, when=None):
        """ Returns True if the course/task is still open """
        if when is None:
            when = datetime.now()

        return self._val[0] <= when and when <= self._val[1]

    def is_always_accessible(self):
        """ Returns true if the course/task is always accessible """
        return self._val[0] == datetime.min and self._val[1] == datetime.max

    def is_never_accessible(self):
        """ Returns true if the course/task is never accessible """
        return self._val[0] == datetime.max and self._val[1] == datetime.max

    def get_std_start_date(self):
        """ If the date is custom, return the start datetime with the format %Y-%m-%d %H:%M:%S. Else, returns "". """
        first, _ = self._val
        if first != datetime.min and first != datetime.max:
            return first.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ""

    def get_std_end_date(self):
        """ If the date is custom, return the end datetime with the format %Y-%m-%d %H:%M:%S. Else, returns "". """
        _, second = self._val
        if second != datetime.max:
            return second.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ""

    def get_start_date(self):
        """ Return a datetime object, representing the date when the task/course become accessible """
        return self._val[0]

    def get_end_date(self):
        """ Return a datetime object, representing the deadline for accessibility """
        return self._val[1]
