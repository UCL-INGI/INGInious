# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Contains AccessibleTime, class that represents the period of time when a course/task is accessible """

from datetime import datetime


def parse_date(date, default=None):
    """
        Parse a valid date
        :param date: string, date to parse
        :param default: datetime object, optionnal, default value to return if date is empty
        :return: datetime object of the parsed date
    """
    if date == "":
        if default is not None:
            return default
        else:
            raise Exception("Empty date given to AccessibleTime")

    if date == "0001-01-01 00:00:00":
        return datetime.min
    if date == "9999-12-31 23:59:59":
        return datetime.max.replace(microsecond=0)

    for format_type in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S",
                        "%d/%m/%Y %H:%M", "%d/%m/%Y %H", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date, format_type)
        except ValueError:
            pass
    raise Exception("Unknown format for " + date)


class AccessibleTime(object):
    """ represents the period of time when a course/task is accessible """

    def __init__(self, period):
        """
            Used to represent the period of time when a course/task is accessible.
            :param val : bool, optionnal, if False, it is never accessible, if True, it is always accessible or limited
            by period dict
            :param period : dict, contains start, end and optionally soft_end as datetime objects or strings
        """

        self.max = datetime.max.replace(microsecond=0)
        self.min = datetime.min

        if not isinstance(period, dict):
            raise Exception("Wrong period given to AccessibleTime")

        # transforming strings into datetimes in case AccessibleTime is used in html files, where datetime objects are not supported
        for key, date in period.items():
            if not isinstance(date, (datetime, str)):
                raise Exception("Wrong period given to AccessibleTime")
            elif isinstance(date, str):
                period[key] = parse_date(date)

        #self._start = self.adapt_database_date(period["start"])
        #self._end = self.adapt_database_date(period["end"])
        self._start = period["start"]
        self._end = period["end"]
        if "soft_end" in period:
            #self._soft_end = self.adapt_database_date(period["soft_end"])
            self._soft_end = period["soft_end"]
            if self._soft_end > self._end:
                self._soft_end = self._end


    # TO REMOVE / CHANGE -> We want the max and min to be stored without milli or microseconds
    def adapt_database_date(self, date):
        """
            Check if the date is the max or min DB value and transforms it into a datetime object.
            MongoDB stores ISODate() objects in the database. When we store datetime.min or datetime.max in the database,
            we will not get the same value back. It is because ISODate() objects store the date with a precision of
            milliseconds, not nanoseconds like datetime objects.
            :param date: datetime object coming from the database
        """
        if date == datetime(1, 1, 1, 0, 0, 0, 000000):
            return datetime.min
        elif date == datetime(9999, 12, 31, 23, 59, 59, 999000):
            return datetime.max.replace(microsecond=0)
        else:
            return date


    def before_start(self, when=None):
        """ Returns True if the task/course is not yet accessible """
        if when is None:
            when = datetime.now()

        return self._start > when

    def after_start(self, when=None):
        """ Returns True if the task/course is or have been accessible in the past """
        return not self.before_start(when)

    def is_open(self, when=None):
        """ Returns True if the course/task is still open """
        if when is None:
            when = datetime.now()

        return self._start <= when and when <= self._end

    def is_open_with_soft_deadline(self, when=None):
        """ Returns True if the course/task is still open with the soft deadline """
        if when is None:
            when = datetime.now()

        return self._start <= when and when <= self._soft_end

    def is_always_accessible(self):
        """ Returns true if the course/task is always accessible """
        return self._start == self.min and self._end == self.max

    def is_never_accessible(self):
        """ Returns true if the course/task is never accessible """
        return self._start == self.max and self._end == self.max

    def get_std_start_date(self):
        """ If the date is custom, return the start datetime with the format %4Y-%m-%d %H:%M:%S. Else, returns "". """
        if self._start != self.min and self._start != self.max:
            return self._start.strftime("%4Y-%m-%d %H:%M:%S")
        else:
            return ""

    def get_std_end_date(self):
        """ If the date is custom, return the end datetime with the format %4Y-%m-%d %H:%M:%S. Else, returns "". """
        if self._end != self.max:
            return self._end.strftime("%4Y-%m-%d %H:%M:%S")
        else:
            return ""

    def get_std_soft_end_date(self):
        """ If the date is custom, return the soft datetime with the format %4Y-%m-%d %H:%M:%S. Else, returns "". """
        if self._soft_end != self.max:
            return self._soft_end.strftime("%4Y-%m-%d %H:%M:%S")
        else:
            return ""

    def get_start_date(self):
        """ Return a datetime object, representing the date when the task/course become accessible """
        return self._start

    def get_end_date(self):
        """ Return a datetime object, representing the deadline for accessibility """
        return self._end

    def get_soft_end_date(self):
        """ Return a datetime object, representing the soft deadline for accessibility """
        return self._soft_end
