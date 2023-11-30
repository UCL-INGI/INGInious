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

    def __init__(self, is_open=None, period=None):
        """
            Used to represent the period of time when a course/task is accessible.
            :param val : bool, optionnal, if False, it is never accessible, if True, it is always accessible or limited
            by period dict
            :param period : dict, contains start, end and optionally soft_end as datetime objects or strings
        """

        if not isinstance(is_open, bool) or not isinstance(period, dict):
            raise Exception("AccessibleTime must be initialized with a boolean and a period dict")

        # transforming strings into datetimes in case AccessibleTime is used in html files (where datetime objects are not supported)
        for key, date in period.items():
            if isinstance(date, str) and date != "":
                period[key] = parse_date(date)
            elif isinstance(date, str) and date == "":
                period[key] = None

        self._start = period["start"] if period["start"] is not None else datetime.min
        self._end = period["end"] if period["end"] is not None else datetime.max
        if "soft_end" in period:
            self._soft_end = period["soft_end"] if period["soft_end"] is not None else datetime.max
            if self._soft_end > self._end:
                self._soft_end = self._end


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
        return self._start == datetime.min and self._end == datetime.max

    def is_never_accessible(self):
        """ Returns true if the course/task is never accessible """
        return self._start == datetime.max and self._end == datetime.max

    def get_std_start_date(self):
        """ If the date is custom, return the start datetime with the format %Y-%m-%d %H:%M:%S. Else, returns "". """
        if self._start != datetime.min and self._start != datetime.max:
            return self._start.strftime("%Y-%m-%d %H:%M:%S") if self._start is not None else ""
        else:
            return ""

    def get_std_end_date(self):
        """ If the date is custom, return the end datetime with the format %Y-%m-%d %H:%M:%S. Else, returns "". """
        if self._end != datetime.max:
            return self._end.strftime("%Y-%m-%d %H:%M:%S") if self._end is not None else ""
        else:
            return ""

    def get_std_soft_end_date(self):
        """ If the date is custom, return the soft datetime with the format %Y-%m-%d %H:%M:%S. Else, returns "". """
        if self._soft_end != datetime.max:
            return self._soft_end.strftime("%Y-%m-%d %H:%M:%S") if self._soft_end is not None else ""
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
