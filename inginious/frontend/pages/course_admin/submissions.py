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

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousAdminPage, INGIniousSubmissionAdminPage
from inginious.frontend.pages.course_admin.statistics import compute_statistics
from inginious.common.base import id_checker


class CourseSubmissionsPage(INGIniousSubmissionAdminPage):
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
        data, limit, above_limit = self.submissions_from_user_input(course, user_input, msgs)  # ONLY audiences user wants to query
        if len(data) == 0 and not self.show_collapse(user_input):
            msgs.append(_("No submissions found"))

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

            archive, error = self.submission_manager.get_submission_archive(course, data,
                                                                            list(reversed(download_type.split('/'))) + [
                                                                                "submissionid"])
            if not error:
                # self._logger.info("Downloading %d submissions from course %s", len(data), course.get_id())
                web.header('Content-Type', 'application/x-gzip', unique=True)
                web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
                return archive
            else:
                msgs.append(_("The following submission could not be prepared for download: {}").format(error))

        if above_limit:
            msgs.append(
                _("The result contains more than {0} submissions. The displayed submissions are truncated. You can modify this value in the advanced query tab.\n").format(
                    limit))

        course_audiences = self.user_manager.get_course_audiences(course)
        return self.template_helper.get_renderer().course_admin.submissions(course, tasks, users, course_audiences,
                                                                            data, statistics, user_input,
                                                                            self._allowed_sort, self._allowed_sort_name,
                                                                            self._valid_formats, msgs,
                                                                            self.show_collapse(user_input))

    def show_collapse(self, user_input):
        """ Return True is we should display the main collapse. """
        # If users has not specified any user/audience, there are no submissions so we display the main collapse.
        if len(user_input['users']) == 0 and len(user_input['audiences']) == 0:
            return True
        return False

    def get_users(self, course):
        """ Returns a sorted list of users """
        users = OrderedDict(sorted(
            list(self.user_manager.get_users_info(self.user_manager.get_course_registered_users(course)).items()),
            key=lambda k: k[1][0] if k[1] is not None else ""))
        return users

    def submissions_from_user_input(self, course, user_input, msgs):
        """ Returns the list of submissions and corresponding aggragations based on inputs """

        submit_time_between = [None, None]
        try:
            if user_input.date_before:
                submit_time_between[1] = user_input.date_before
            if user_input.date_after:
                submit_time_between[0] = user_input.date_after
        except ValueError:  # If match of datetime.strptime() fails
            msgs.append(_("Invalid dates"))

        tags = None
        if len(user_input.filter_tags) == len(user_input.filter_tags_presence):
            tags = [(a, b in ["True", "true"]) for a, b in zip(user_input.filter_tags, user_input.filter_tags_presence)]

        must_keep_best_submissions_only = "eval" in user_input or (
                "eval_dl" in user_input and "download" in web.input())

        limit = self._trunc_limit
        try:
            ulimit = int(user_input.limit) if user_input.limit else 0
            if ulimit > 0:
                limit = ulimit
        except ValueError:
            msgs.append(_("Invalid limit"))

        data = self.get_selected_submissions(course, only_tasks=user_input.tasks,
                                             only_tasks_with_categories=user_input.org_tags,
                                             only_users=user_input.users,
                                             only_audiences=user_input.audiences,
                                             with_tags=tags,
                                             grade_between=[
                                                 float(user_input.grade_min) if user_input.grade_min else None,
                                                 float(user_input.grade_max) if user_input.grade_max else None
                                             ],
                                             submit_time_between=submit_time_between,
                                             keep_only_evaluation_submissions=must_keep_best_submissions_only,
                                             sort_by=(user_input.sort_by, user_input.order == "1"),
                                             limit=limit+1)

        data = [dict(list(f.items()) + [("url", self.submission_url_generator(str(f["_id"])))]) for f in data]
        return data[0:limit], limit, len(data) > limit

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
