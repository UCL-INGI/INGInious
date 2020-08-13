# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import pymongo
import web
from collections import OrderedDict
from bson import ObjectId
from datetime import datetime

from inginious.common.base import id_checker
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class CourseSubmissionsNewPage(INGIniousAdminPage):
    """ Page that allow search, view, replay an download of submisssions done by students """

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request """
        course, __ = self.get_course_and_check_rights(courseid)
        msgs = []

        user_input = web.input(
            users=[],
            audiences=[],
            tasks=[],
            org_tags=[]
        )
        params = self.get_params(user_input, course)

        return self.page(course, params, msgs)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        user_input = web.input(
            users=[],
            audiences=[],
            tasks=[],
            org_tags=[]
        )
        params = self.get_params(user_input, course)

        return self.page(course, params)

    def page(self, course, params, msgs=None):
        """ Get all data and display the page """
        msgs = msgs if msgs else []

        users = self.get_users(course)
        audiences = self.user_manager.get_course_audiences(course)
        tasks = course.get_tasks()

        tutored_audiences = [str(audience["_id"]) for audience in audiences if
                             self.user_manager.session_username() in audience["tutors"]]
        tutored_users = []
        for audience in audiences:
            if self.user_manager.session_username() in audience["tutors"]:
                tutored_users += audience["students"]

        try:
            new_limit = int(params.get("limit", 50))
            limit = new_limit if new_limit > 0 else 50
        except TypeError:
            limit = 50

        data = self.submissions_from_user_input(course, params, msgs, limit)

        return self.template_helper.get_renderer().course_admin.new_submissions(course, users, tutored_users, audiences,
                                                                                tutored_audiences, tasks, params, data,
                                                                                msgs)

    def get_users(self, course):
        user_ids = self.user_manager.get_course_registered_users(course)
        users = {user: self.user_manager.get_user_realname(user) for user in user_ids}
        return OrderedDict(sorted(users.items(), key=lambda x: x[1]))

    def get_params(self, user_input, course):
        users = self.get_users(course)
        audiences = self.user_manager.get_course_audiences(course)
        tasks = course.get_tasks()

        # Sanitise user
        if not user_input.get("users", []) and not user_input.get("audiences", []):
            user_input["users"] = list(users.keys())
        if len(user_input.get("users", [])) == 1 and "," in user_input["users"][0]:
            user_input["users"] = user_input["users"][0].split(',')
        user_input["users"] = [user for user in user_input["users"] if user in users]

        # Sanitise audiences
        if len(user_input.get("audiences", [])) == 1 and "," in user_input["audiences"][0]:
            user_input["audiences"] = user_input["audiences"][0].split(',')
        user_input["audiences"] = [audience for audience in user_input["audiences"] if any(str(a["_id"]) == audience for a in audiences)]

        # Sanitise tasks
        if not user_input.get("tasks", []):
            user_input["tasks"] = list(tasks.keys())
        if len(user_input.get("tasks", [])) == 1 and "," in user_input["tasks"][0]:
            user_input["tasks"] = user_input["tasks"][0].split(',')
        user_input["tasks"] = [task for task in user_input["tasks"] if task in tasks]

        # Sanitise tags
        if not user_input.get("tasks", []):
            user_input["tasks"] = []
        if len(user_input.get("org_tags", [])) == 1 and "," in user_input["org_tags"][0]:
            user_input["org_tags"] = user_input["org_tags"][0].split(',')
        user_input["org_tags"] = [org_tag for org_tag in user_input["org_tags"] if org_tag in course.get_tags()]

        # Sanitise grade
        if "grade_min" in user_input:
            try:
                user_input["grade_min"] = int(user_input["grade_min"])
            except:
                user_input["grade_min"] = ''
        if "grade_max" in user_input:
            try:
                user_input["grade_max"] = int(user_input["grade_max"])
            except:
                user_input["grade_max"] = ''

        # Sanitise order
        if "sort_by" in user_input and user_input["sort_by"] not in ["submitted_on", "username", "grade", "taskid"]:
            user_input["sort_by"] = "submitted_on"
        if "order" in user_input:
            try:
                user_input["order"] = 1 if int(user_input["order"]) == 1 else 0
            except:
                user_input["order"] = 0

        # Sanitise limit
        if "limit" in user_input:
            try:
                user_input["limit"] = int(user_input["limit"])
            except:
                user_input["limit"] = 500

        return user_input

    def submissions_from_user_input(self, course, user_input, msgs, limit=None):
        """ Returns the list of submissions and corresponding aggragations based on inputs """

        submit_time_between = [None, None]
        try:
            if user_input.get('date_before', ''):
                submit_time_between[1] = user_input["date_before"]
            if user_input.get('date_after', ''):
                submit_time_between[0] = user_input["date_after"]
        except ValueError:  # If match of datetime.strptime() fails
            msgs.append(_("Invalid dates"))

        must_keep_best_submissions_only = "eval" in user_input or (
                "eval_dl" in user_input and "download" in web.input())

        return self.get_selected_submissions(course, only_tasks=user_input["tasks"],
                                             only_tasks_with_categories=user_input["org_tags"],
                                             only_users=user_input["users"],
                                             only_audiences=user_input["audiences"],
                                             grade_between=[
                                                 float(user_input["grade_min"]) if user_input.get('grade_min', '') else None,
                                                 float(user_input["grade_max"]) if user_input.get('grade_max', '') else None
                                             ],
                                             submit_time_between=submit_time_between,
                                             keep_only_evaluation_submissions=must_keep_best_submissions_only,
                                             keep_only_crashes="crashes_only" in user_input,
                                             sort_by=(user_input.get('sort_by', 'submitted_on'), user_input.get('order', 0) == 1),
                                             limit=limit)

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
                                 keep_only_crashes=False,
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
        :param keep_only_crashes: True to keep only submissions that timed out or crashed
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

        # Only crashed or timed-out submissions
        if keep_only_crashes:
            filter["result"] = {"$in": ["crash", "timeout"]}

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
