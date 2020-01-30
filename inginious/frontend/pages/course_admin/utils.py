# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for administration pages """

import codecs
import csv
import io
from collections import OrderedDict
from datetime import datetime

import pymongo
import web
from bson.objectid import ObjectId

from inginious.common.base import id_checker
from inginious.frontend.pages.utils import INGIniousAuthPage


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

    def _validate_list(self, list_of_ids):
        """ Prevent MongoDB injections by verifying arrays sent to it """
        for i in list_of_ids:
            if not id_checker(i):
                raise web.notfound()

    def get_selected_submissions(self, course,
                                 only_tasks=None, only_tasks_with_categories=None,
                                 only_users=None, only_audiences=None,
                                 with_tags=None,
                                 grade_between=None, submit_time_between=None,
                                 keep_only_evaluation_submissions=False,
                                 sort_by=("submitted_on", True),
                                 limit=None):
        """
        All the parameters (excluding course, sort_by and keep_only_evaluation_submissions) can be None.
        If that is the case, they are ignored.

        :param course: the course
        :param only_tasks: a list of task ids. Only submissions on these tasks will be loaded.
        :param only_tasks_with_categories: keep only tasks that have a least one category in common with this list
        :param only_users: a list of usernames. Only submissions from these users will be loaded.
        :param only_audiences: a list of audience ids. Only submissions from users in these will be loaded
        :param with_tags: a list of tags in the form [(tagid, present)], where present is a boolean indicating
               whether the tag MUST be present or MUST NOT be present. If you don't mind if a tag is present or not,
               just do not put it in the list.
        :param grade_between: a tuple of two floating point number or None ([0.0, None], [None, 0.0] or [None, None])
               that indicates bounds on the grade of the retrieved submissions
        :param submit_time_between: a tuple of two dates or None ([datetime, None], [None, datetime] or [None, None])
               that indicates bounds on the submission time of the submission. Format: "%Y-%m-%d %H:%M:%S"
        :param keep_only_evaluation_submissions: True to keep only submissions that are counting for the evaluation
        :param sort_by: a tuple (sort_column, ascending) where sort_column is in ["submitted_on", "username", "grade", "taskid"]
               and ascending is either True or False.
        :param limit: an integer representing the maximum number of submission to list.
        :return: a list of submission filling the criterias above.
        """
        # Create the filter for the query. base_filter is used to also filter the collection user_tasks.
        base_filter = {"courseid": course.get_id()}
        filter = {}

        # Tasks (with categories)
        if only_tasks and not only_tasks_with_categories:
            self._validate_list(only_tasks)
            base_filter["taskid"] = {"$in": only_tasks}
        elif only_tasks_with_categories:
            only_tasks_with_categories = set(only_tasks_with_categories)
            more_tasks = {taskid for taskid, task in course.get_tasks().items() if
                          only_tasks_with_categories.intersection(task.get_categories())}
            if only_tasks:
                self._validate_list(only_tasks)
                more_tasks.intersection_update(only_tasks)
            base_filter["taskid"] = {"$in": list(more_tasks)}

        # Users/audiences
        if only_users and not only_audiences:
            self._validate_list(only_users)
            base_filter["username"] = {"$in": only_users}
        elif only_audiences:
            list_audience_id = [ObjectId(o) for o in only_audiences]
            students = set()
            for audience in self.database.audiences.find({"_id": {"$in": list_audience_id}}):
                students.update(audience["students"])
            if only_users:  # do the intersection
                self._validate_list(only_users)
                students.intersection_update(only_users)
            base_filter["username"] = {"$in": list(students)}

        # Tags
        for tag_id, should_be_present in with_tags or []:
            if id_checker(tag_id):
                filter["tests." + tag_id] = {"$in": [None, False]} if not should_be_present else True

        # Grades
        if grade_between and grade_between[0] is not None:
            filter.setdefault("grade", {})["$gte"] = float(grade_between[0])
        if grade_between and grade_between[1] is not None:
            filter.setdefault("grade", {})["$lte"] = float(grade_between[1])

        # Submit time
        try:
            if submit_time_between and submit_time_between[0] is not None:
                filter.setdefault("submitted_on", {})["$gte"] = datetime.strptime(submit_time_between[0], "%Y-%m-%d %H:%M:%S")
            if submit_time_between and submit_time_between[1] is not None:
                filter.setdefault("submitted_on", {})["$lte"] = datetime.strptime(submit_time_between[1], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # TODO it would be nice to display this in the interface. However, this should never happen because
            # we have a nice JS interface that prevents this.
            pass

        # Only evaluation submissions
        user_tasks = self.database.user_tasks.find(base_filter)
        best_submissions_list = {user_task['submissionid'] for user_task in user_tasks if
                                 user_task['submissionid'] is not None}

        if keep_only_evaluation_submissions is True:
            filter["_id"] = {"$in": list(best_submissions_list)}

        filter.update(base_filter)
        submissions = self.database.submissions.find(filter)

        if sort_by[0] not in ["submitted_on", "username", "grade", "taskid"]:
            sort_by[0] = "submitted_on"
        submissions = submissions.sort(sort_by[0], pymongo.ASCENDING if sort_by[1] else pymongo.DESCENDING)

        if limit is not None:
            submissions.limit(limit)

        out = list(submissions)

        for d in out:
            d["best"] = d["_id"] in best_submissions_list  # mark best submissions

        return out

    def show_page_params(self, course, user_input):
        tasks = sorted(list(course.get_tasks().items()), key=lambda task: (task[1].get_order(), task[1].get_id()))

        user_list = self.user_manager.get_course_registered_users(course, False)
        users = OrderedDict(sorted(list(self.user_manager.get_users_info(user_list).items()),
                                   key=lambda k: k[1][0] if k[1] is not None else ""))
        user_data = OrderedDict(
            [(username, user[0] if user is not None else username) for username, user in users.items()])

        audiences = self.user_manager.get_course_audiences(course)
        tutored_audiences = [str(audience["_id"]) for audience in audiences if
                                self.user_manager.session_username() in audience["tutors"]]

        tutored_users = []
        for audience in audiences:
            if self.user_manager.session_username() in audience["tutors"]:
                tutored_users += audience["students"]

        checked_tasks = list(course.get_tasks().keys())
        checked_users = list(user_data.keys())
        checked_audiences = [audience['_id'] for audience in audiences]
        show_audiences = False

        if "tasks" in user_input:
            checked_tasks = user_input.tasks if isinstance(user_input.tasks, list) else user_input.tasks.split(',')
        if "users" in user_input:
            checked_users = user_input.users if isinstance(user_input.users, list) else user_input.users.split(',')
        if "audiences" in user_input:
            checked_audiences = user_input.audiences if isinstance(user_input.audiences, list) else user_input.audiences.split(',')
            show_audiences = True
        if "tutored" in user_input:
            if user_input.tutored == "audiences":
                checked_audiences = tutored_audiences
                show_audiences = True
            elif user_input.tutored == "users":
                checked_users = tutored_users
                show_audiences = True

        for audience in audiences:
            audience['checked'] = str(audience['_id']) in checked_audiences

        return tasks, user_data, audiences, tutored_audiences, tutored_users, checked_tasks, checked_users, show_audiences

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
        default_entries += [("settings", "<i class='fa fa-cog fa-fw'></i>&nbsp; " + _("Course settings"))]

    default_entries += [("stats", "<i class='fa fa-area-chart fa-fw'></i>&nbsp; " + _("Stats")),
                        ("students", "<i class='fa fa-user fa-fw'></i>&nbsp; " + _("Students")),
                        ("audiences", "<i class='fa fa-group fa-fw'></i>&nbsp; " + _("Audiences"))]

    if not course.is_lti():
        default_entries += [("groups", "<i class='fa fa-group fa-fw'></i>&nbsp; " +_("Groups"))]

    default_entries += [("tasks", "<i class='fa fa-tasks fa-fw'></i>&nbsp; " + _("Tasks")),
                        ("tags", "<i class='fa fa-tags fa-fw'></i>&nbsp;" + _("Tags")),
                        ("submissions", "<i class='fa fa-search fa-fw'></i>&nbsp; " + _("View submissions")),
                        ("download", "<i class='fa fa-download fa-fw'></i>&nbsp; " + _("Download submissions"))]

    if user_manager.has_admin_rights_on_course(course):
        default_entries += [("replay", "<i class='fa fa-refresh fa-fw'></i>&nbsp; " + _("Replay submissions")),
                            ("danger", "<i class='fa fa-bomb fa-fw'></i>&nbsp; " + _("Danger zone"))]

    # Hook should return a tuple (link,name) where link is the relative link from the index of the course administration.
    additional_entries = [entry for entry in plugin_manager.call_hook('course_admin_menu', course=course) if entry is not None]

    return renderer.course_admin.menu(course, default_entries + additional_entries, current)


class CourseRedirect(INGIniousAdminPage):
    """ Redirect admins to /settings and tutors to /task """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        if self.user_manager.session_username() in course.get_tutors():
            raise web.seeother(self.app.get_homepath() + '/admin/{}/tasks'.format(courseid))
        else:
            raise web.seeother(self.app.get_homepath() + '/admin/{}/settings'.format(courseid))

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        return self.GET_AUTH(courseid)
