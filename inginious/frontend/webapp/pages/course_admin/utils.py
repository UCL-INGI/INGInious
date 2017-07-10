# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for administration pages """

import io
import codecs
import csv

import web
from bson.objectid import ObjectId
from inginious.common.base import id_checker
from collections import OrderedDict
from inginious.frontend.webapp.pages.utils import INGIniousAuthPage


class INGIniousAdminPage(INGIniousAuthPage):
    """
    An improved version of INGIniousAuthPage that checks rights for the administration
    """

    def get_course_and_check_rights(self, courseid, taskid=None, allow_all_staff=True):
        """ Returns the course with id ``courseid`` and the task with id ``taskid``, and verify the rights of the user.
            Raise web.notfound() when there is no such course of if the users has not enough rights.

            :param courseid: the course on which to check rights
            :param taskid: If not None, returns also the task with id ``taskid``
            :param allow_all_staff: allow admins AND tutors to see the page. If false, all only admins.
            :returns (Course, Task)
        """

        try:
            course = self.course_factory.get_course(courseid)
            if allow_all_staff:
                if not self.user_manager.has_staff_rights_on_course(course):
                    raise web.notfound()
            else:
                if not self.user_manager.has_admin_rights_on_course(course):
                    raise web.notfound()

            if taskid is None:
                return course, None
            else:
                return course, course.get_task(taskid)
        except:
            raise web.notfound()


class INGIniousSubmissionAdminPage(INGIniousAdminPage):
    """
    An INGIniousAdminPage containing some common methods between download/replay pages
    """

    def _validate_list(self, usernames):
        """ Prevent MongoDB injections by verifying arrays sent to it """
        for i in usernames:
            if not id_checker(i):
                raise web.notfound()

    def get_selected_submissions(self, course, filter_type, selected_tasks, users, aggregations, stype):
        """
        Returns the submissions that have been selected by the admin
        :param course: course
        :param filter_type: users or aggregations
        :param selected_tasks: selected tasks id
        :param users: selected usernames
        :param aggregations: selected aggregations
        :param stype: single or all submissions
        :return:
        """
        if filter_type == "users":
            self._validate_list(users)
            aggregations = list(self.database.aggregations.find({"courseid": course.get_id(),
                                                                 "students": {"$in": users}}))
            # Tweak if not using classrooms : classroom['students'] may content ungrouped users
            aggregations = dict([(username,
                                  aggregation if course.use_classrooms() or (
                                      username in aggregation['groups'][0]["students"]) else None
                                  ) for aggregation in aggregations for username in users])

        else:
            self._validate_list(aggregations)
            aggregations = list(
                self.database.aggregations.find({"_id": {"$in": [ObjectId(cid) for cid in aggregations]}}))

            # Tweak if not using classrooms : classroom['students'] may content ungrouped users
            aggregations = dict([(username,
                                  aggregation if course.use_classrooms() or (
                                  username in aggregation['groups'][0]["students"]) else None
                                  ) for aggregation in aggregations for username in aggregation["students"]])

        if stype == "single":
            user_tasks = list(self.database.user_tasks.find({"username": {"$in": list(aggregations.keys())},
                                                             "taskid": {"$in": selected_tasks},
                                                             "courseid": course.get_id()}))

            submissionsid = [user_task['submissionid'] for user_task in user_tasks if user_task['submissionid'] is not None]
            submissions = list(self.database.submissions.find({"_id": {"$in": submissionsid}}))
        else:
            submissions = list(self.database.submissions.find({"username": {"$in": list(aggregations.keys())},
                                                               "taskid": {"$in": selected_tasks},
                                                               "courseid": course.get_id(),
                                                               "status": {"$in": ["done", "error"]}}))

        return submissions, aggregations

    def show_page_params(self, course, user_input):
        tasks = sorted(list(course.get_tasks().items()), key=lambda task: (task[1].get_order(), task[1].get_id()))

        user_list = self.user_manager.get_course_registered_users(course, False)
        users = OrderedDict(sorted(list(self.user_manager.get_users_info(user_list).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else ""))
        user_data = OrderedDict(
            [(username, user[0] if user is not None else username) for username, user in users.items()])

        aggregations = self.user_manager.get_course_aggregations(course)
        tutored_aggregations = [str(aggregation["_id"]) for aggregation in aggregations if
                                self.user_manager.session_username() in aggregation["tutors"] and len(
                                    aggregation['groups']) > 0]

        tutored_users = []
        for aggregation in aggregations:
            for username in aggregation["students"]:
                # If no classrooms used, only students inside groups
                if self.user_manager.session_username() in aggregation["tutors"] and \
                        (course.use_classrooms() or
                             (len(aggregation['groups']) > 0 and username in aggregation['groups'][0]['students'])):
                    tutored_users += [username]

        checked_tasks = list(course.get_tasks().keys())
        checked_users = list(user_data.keys())
        checked_aggregations = [aggregation['_id'] for aggregation in aggregations]
        show_aggregations = False

        if "tasks" in user_input:
            checked_tasks = user_input.tasks.split(',')
        if "users" in user_input:
            checked_users = user_input.users.split(',')
        if "aggregations" in user_input:
            checked_aggregations = user_input.aggregations.split(',')
            show_aggregations = True
        if "tutored" in user_input:
            if user_input.tutored == "aggregations":
                checked_aggregations = tutored_aggregations
                show_aggregations = True
            elif user_input.tutored == "users":
                checked_users = tutored_users
                show_aggregations = True

        for aggregation in aggregations:
            aggregation['checked'] = str(aggregation['_id']) in checked_aggregations

        return tasks, user_data, aggregations, tutored_aggregations, tutored_users, checked_tasks, checked_users, show_aggregations

class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = io.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        """ Writes a row to the CSV file """
        self.writer.writerow(row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)
        self.queue.seek(0)

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
        for key, val in rval.items():
            if isinstance(val, dict):
                for key2, val2 in val.items():
                    toadd[str(key) + "[" + str(key2) + "]"] = val2
                todel.append(key)
        for k in todel:
            del rval[k]
        for k, v in toadd.items():
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
                new_output.append(str(data[entry][col]) if col in data[entry] else "")
            output.append(new_output)
    else:
        for entry in data:
            new_output = []
            for col in columns:
                new_output.append(str(entry[col]) if col in entry else "")
            output.append(new_output)

    csv_string = io.StringIO()
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
        default_entries += [("settings", "<i class='fa fa-cog fa-fw'></i>&nbsp; Course settings")]

    default_entries += [("students", "<i class='fa fa-user fa-fw'></i>&nbsp; Students")]

    if not course.is_lti():
        default_entries += [("aggregations", "<i class='fa fa-group fa-fw'></i>&nbsp; " +
                             ("Classrooms" if course.use_classrooms() else "Teams"))]

    default_entries += [("tasks", "<i class='fa fa-tasks fa-fw'></i>&nbsp; Tasks"),
                        ("download", "<i class='fa fa-download fa-fw'></i>&nbsp; Download submissions")]

    if user_manager.has_admin_rights_on_course(course):
        default_entries += [("replay", "<i class='fa fa-refresh fa-fw'></i>&nbsp; Replay submissions"),
                             ("danger", "<i class='fa fa-bomb fa-fw'></i>&nbsp; Danger zone")]

    # Hook should return a tuple (link,name) where link is the relative link from the index of the course administration.
    additional_entries = [entry for entry in plugin_manager.call_hook('course_admin_menu', course=course) if entry is not None]

    return renderer.course_admin.menu(course, default_entries + additional_entries, current)


class CourseRedirect(INGIniousAdminPage):
    """ Redirect admins to /settings and tutors to /task """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, _ = self.get_course_and_check_rights(courseid)
        if self.user_manager.session_username() in course.get_tutors():
            raise web.seeother(self.app.get_homepath() + '/admin/{}/tasks'.format(courseid))
        else:
            raise web.seeother(self.app.get_homepath() + '/admin/{}/settings'.format(courseid))

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        return self.GET_AUTH(courseid)
