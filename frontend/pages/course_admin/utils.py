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
""" Utilities for administration pages """

import StringIO
import cStringIO
import codecs
import csv

import web
from frontend.custom.courses import FrontendCourse
import frontend.user as User


def get_course_and_check_rights(courseid, taskid=None):
    """ Return the course with id, and verify the rights of the user to administer it.
        Raise web.notfound() when there is no such course of if the users has not enough rights.
        If taskid is not None, also returns tyhe tuple (course, task). """
    try:
        if User.is_logged_in():
            course = FrontendCourse(courseid)
            if User.get_username() not in course.get_admins():
                raise web.notfound()

            if taskid is None:
                return course
            else:
                return (course, course.get_task(taskid))
        else:
            raise web.notfound()
    except:
        web.notfound()


class UnicodeWriter(object):

    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        """ Writes a row to the CSV file """
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        """ Writes multiple rows to the CSV file """
        for row in rows:
            self.writerow(row)


def make_csv(data):
    """ Returns the content of a CSV file with the data of the dict/list data """
    columns = set()
    output = [[]]
    if isinstance(data, dict):
        output[0].append("id")
        for entry in data:
            for col in data[entry]:
                columns.add(col)
    else:
        for entry in data:
            for col in entry:
                columns.add(col)

    for col in columns:
        output[0].append(col)

    if isinstance(data, dict):
        for entry in data:
            new_output = [str(entry)]
            for col in columns:
                new_output.append(unicode(data[entry][col]) if col in data[entry] else "")
            output.append(new_output)
    else:
        for entry in data:
            new_output = []
            for col in columns:
                new_output.append(unicode(entry[col]) if col in entry else "")
            output.append(new_output)

    csv_string = StringIO.StringIO()
    csv_writer = UnicodeWriter(csv_string)
    for row in output:
        csv_writer.writerow(row)
    csv_string.seek(0)
    web.header('Content-Type', 'text/csv; charset=utf-8')
    web.header('Content-disposition', 'attachment; filename=export.csv')
    return csv_string.read()
