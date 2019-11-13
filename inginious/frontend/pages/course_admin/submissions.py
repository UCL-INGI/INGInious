# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pymongo
import web
import re
import itertools
import gettext
from datetime import datetime
from bson.objectid import ObjectId
from collections import OrderedDict

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage
from inginious.frontend.pages.course_admin.statistics import compute_statistics
from inginious.common.base import id_checker


class CourseSubmissionsPage(INGIniousAdminPage):
    """ List information about a task done by a student """

    _allowed_sort = ["submitted_on", "username", "grade", "taskid"]
    _allowed_sort_name = [_("Submitted on"), _("User"), _("Grade"), _("Task id")]
    _valid_formats = ["taskid/username", "taskid/audience", "username/taskid", "audience/taskid"]
    _valid_formats_name = [_("taskid/username"), _("taskid/audience"), _("username/taskid"), _("audience/taskid")]
    _trunc_limit = 500  # To trunc submissions if there are too many submissions

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        msgs = []

        if "replay" in web.input():
            if not self.user_manager.has_admin_rights_on_course(course):
                raise web.notfound()
            
            input = self.get_input()
            tasks = course.get_tasks()
            data, __ = self.get_submissions(course, input)
            for submission in data:
                self.submission_manager.replay_job(tasks[submission["taskid"]], submission)
            msgs.append(_("{0} selected submissions were set for replay.").format(str(len(data))))
            
        return self.page(course, msgs)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        return self.page(course)

    def submission_url_generator(self, submissionid):
        """ Generates a submission url """
        return "?submission=" + submissionid

    def page(self, course, msgs=None):
        """ Get all data and display the page """
        msgs = msgs if msgs else []
        
        user_input = self.get_input()
        data, audience = self.get_submissions(course, user_input)  # ONLY audiences user wants to query
        if len(data) == 0 and not self.show_collapse(user_input):
            msgs.append(_("No submissions found"))

        audiences = self.user_manager.get_course_audiences(course)  # ALL audiences of the course
        audiences_id = [audience["_id"] for audience in audiences]
        audiences_list = list(self.database.audiences.aggregate([
            {"$match": {"_id": {"$in": audiences_id}}},
            {"$unwind": "$students"},
            {"$project": {
                "audience": "$_id",
                "students": 1
            }}
        ]))
        audiences = {audience["_id"]: audience for audience in audiences}
        audiences = {d["students"]: audiences[d["audience"]] for d in audiences_list}

        users = self.get_users(course)  # All users of the course
        tasks = course.get_tasks()  # All tasks of the course

        statistics = None
        if user_input.stat != "no_stat":
            statistics = compute_statistics(tasks, data, True if "with_pond_stat" == user_input.stat else False)

        if "csv" in web.input():
            return make_csv(data)
                        
        if "download" in web.input():
            download_type = web.input(download_type=self._valid_formats[0]).download_type
            if download_type not in self._valid_formats:
                download_type = self._valid_formats[0]

            archive, error = self.submission_manager.get_submission_archive(data, list(reversed(download_type.split('/'))), audiences)
            if not error:
                # self._logger.info("Downloading %d submissions from course %s", len(data), course.get_id())
                web.header('Content-Type', 'application/x-gzip', unique=True)
                web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
                return archive
            else:
                msgs.append(_("The following submission could not be prepared for download: {}").format(error))

        if user_input.limit != '' and user_input.limit.isdigit():
            data = data[:int(user_input.limit)]
            
        if len(data) > self._trunc_limit:
            msgs.append(_("The result contains more than {0} submissions. The displayed submissions are truncated.\n").format(self._trunc_limit))
            data = data[:self._trunc_limit]
        return self.template_helper.get_renderer().course_admin.submissions(course, tasks, users, audiences, data, statistics, user_input, self._allowed_sort, self._allowed_sort_name, self._valid_formats, msgs, self.show_collapse(user_input))

    def show_collapse(self, user_input):
        """ Return True is we should display the main collapse. """
        # If users has not specified any user/audience, there are no submissions so we display the main collapse.
        if len(user_input['users']) == 0 and len(user_input['audiences']) == 0:
            return True
        return False

    def get_users(self, course):
        """ Returns a sorted list of users """
        users = OrderedDict(sorted(list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course)).items()),
            key=lambda k: k[1][0] if k[1] is not None else ""))
        return users
        
    def get_submissions(self, course, user_input):
        """ Returns the list of submissions and corresponding aggragations based on inputs """

        # Build lists of wanted users based on audiences and specific users
        list_audience_id = [ObjectId(o) for o in user_input.audiences]
        audience = list(self.database.audiences.find({"_id": {"$in": list_audience_id}}))
        more_username = [s["students"] for s in audience]  # Extract usernames of students
        more_username = [y for x in more_username for y in x]  # Flatten lists
        
        # Get tasks based on categories
        categories = set(user_input.org_tags)
        more_tasks = [taskid for taskid, task in course.get_tasks().items() if categories.intersection(task.get_categories())]

        # Base query
        query_base = {"courseid": course.get_id()}

        students = user_input.users + more_username
        if len(students):
            query_base["username"] = {"$in": students}

        tasks = user_input.tasks + more_tasks
        if len(tasks):
            query_base["taskid"] = {"$in": tasks}

        if not len(tasks) and not len(students):
            return {}, {}

        # Additional query field
        query_advanced = {}
        if user_input.grade_min:
            query_advanced.setdefault("grade", {})["$gte"] = float(user_input.grade_min)
        if user_input.grade_max:
            query_advanced.setdefault("grade", {})["$lte"] = float(user_input.grade_max)

        try:
            if user_input.date_before:
                query_advanced.setdefault("submitted_on", {})["$lte"] = datetime.strptime(user_input.date_before, "%Y-%m-%d %H:%M:%S")
            if user_input.date_after:
                query_advanced.setdefault("submitted_on", {})["$gte"] = datetime.strptime(user_input.date_after, "%Y-%m-%d %H:%M:%S")
        except ValueError:  # If match of datetime.strptime() fails
            pass
        
        # Query with tags
        if len(user_input.filter_tags) == len(user_input.filter_tags_presence):
            for i in range(0, len(user_input.filter_tags)):
                if id_checker(user_input.filter_tags[i]):
                    state = (user_input.filter_tags_presence[i] in ["True", "true"])
                    query_advanced["tests." + user_input.filter_tags[i]] = {"$in": [None, False]} if not state else True
            
        # Mongo operations
        data = list(self.database.submissions.find({**query_base, **query_advanced}).sort([(user_input.sort_by, 
            pymongo.DESCENDING if user_input.order == "0" else pymongo.ASCENDING)]))
        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]

        # Get best submissions from database
        user_tasks = list(self.database.user_tasks.find(query_base, {"submissionid": 1, "_id": 0}))
        best_submissions_list = [u["submissionid"] for u in user_tasks]  # list containing ids of best submissions
        for d in data:
            d["best"] = d["_id"] in best_submissions_list  # mark best submissions

        # Keep best submissions
        if "eval" in user_input or ("eval_dl" in user_input and "download" in web.input()):
            data = [d for d in data if d["best"]]
        return data, audience

    def get_input(self):
        """ Loads web input, initialise default values and check/sanitise some inputs from users """
        user_input = web.input(
            users=[],
            tasks=[],
            audiences=[],
            org_tags=[],
            grade_min='',
            grade_max='',
            sort_by="submitted_on",
            order='0',  # "0" for pymongo.DESCENDING, anything else for pymongo.ASCENDING
            limit='',
            filter_tags=[],
            filter_tags_presence=[],
            date_after='',
            date_before='',
            stat='with_stat',
        )

        # Sanitise inputs
        for item in itertools.chain(user_input.tasks, user_input.audiences):
            if not id_checker(item):
                raise web.notfound()

        if user_input.sort_by not in self._allowed_sort:
            raise web.notfound()

        digits = [user_input.grade_min, user_input.grade_max, user_input.order, user_input.limit]
        for d in digits:
            if d != '' and not d.isdigit():
                raise web.notfound()

        return user_input 
