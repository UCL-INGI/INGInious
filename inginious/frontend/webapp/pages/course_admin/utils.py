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
""" Utilities for administration pages """

import StringIO
import cStringIO
import codecs
import csv

import web

from inginious.frontend.webapp.pages.utils import INGIniousPage


class INGIniousAdminPage(INGIniousPage):
    """
    An improved version of INGIniousPage that checks rights for the administration
    """

    def get_course_and_check_rights(self, courseid, taskid=None, allow_all_staff=True):
        """ Returns the course with id ```courseid``` and the task with id ```taskid```, and verify the rights of the user.
            Raise web.notfound() when there is no such course of if the users has not enough rights.

            :param courseid: the course on which to check rights
            :param taskid: If not None, returns also the task with id ```taskid```
            :param allow_all_staff: allow admins AND tutors to see the page. If false, all only admins.
            :returns (Course, Task)
        """

        try:
            if self.user_manager.session_logged_in():
                course = self.course_factory.get_course(courseid)
                if allow_all_staff:
                    if not self.user_manager.has_staff_rights_on_course(course):
                        raise web.notfound()
                else:
                    if not self.user_manager.has_admin_rights_on_course(course):
                        raise web.notfound()

                if taskid is None:
                    return (course, None)
                else:
                    return (course, course.get_task(taskid))
            else:
                raise web.notfound()
        except:
            raise web.notfound()


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
    # Convert sub-dicts to news cols
    for entry in data:
        rval = entry
        if isinstance(data, dict):
            rval = data[entry]
        todel = []
        toadd = {}
        for key, val in rval.iteritems():
            if isinstance(val, dict):
                for key2, val2 in val.iteritems():
                    toadd[str(key) + "[" + str(key2) + "]"] = val2
                todel.append(key)
        for k in todel:
            del rval[k]
        for k, v in toadd.iteritems():
            rval[k] = v

    # Convert everything to CSV
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

    columns = sorted(columns)

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


def get_menu(course, current, renderer, plugin_manager, user_manager):
    """ Returns the HTML of the menu used in the administration. ```current``` is the current page of section """
    default_entries = []
    if user_manager.has_admin_rights_on_course(course):
        default_entries += [("settings", "<i class='fa fa-cog fa-fw'></i>&nbsp; Course settings"),
                            ("batch", "<i class='fa fa-rocket fa-fw'></i>&nbsp; Batch operations")]

    default_entries += [("students", "<i class='fa fa-user fa-fw'></i>&nbsp; Students"),
                        ("classrooms", "<i class='fa fa-group fa-fw'></i>&nbsp; Classrooms")]

    default_entries += [("tasks", "<i class='fa fa-tasks fa-fw'></i>&nbsp; Tasks"),
                        ("download", "<i class='fa fa-download fa-fw'></i>&nbsp; Download submissions")]

    # Hook should return a tuple (link,name) where link is the relative link from the index of the course administration.
    additionnal_entries = [entry for entry in plugin_manager.call_hook('course_admin_menu', course=course) if entry is not None]

    return renderer.course_admin.menu(course, default_entries + additionnal_entries, current)


class CourseRedirect(INGIniousAdminPage):
    """ Redirect admins to /settings and tutors to /task """

    def GET(self, courseid):
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        if self.user_manager.session_username() in course.get_tutors():
            raise web.seeother('/admin/{}/tasks'.format(courseid))
        else:
            raise web.seeother('/admin/{}/settings'.format(courseid))

    def POST(self, courseid):
        """ POST request """
        return self.GET(courseid)
