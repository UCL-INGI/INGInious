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
from bson.objectid import ObjectId
import web

from frontend.base import get_database
from frontend.base import renderer
from frontend.pages.course_admin.utils import get_course_and_check_rights
from frontend.submission_manager import get_submission_archive

class DownloadSubmissionFiles(object):
    """ List informations about all tasks """

    def GET(self, courseid):
        """ GET request """
        course, _ = get_course_and_check_rights(courseid)
        user_input = web.input()
        if "dl" in user_input:
            include_old_submissions = "include_all" in user_input

            if user_input['dl'] == 'submission':
                return self.download_submission(user_input['id'], include_old_submissions)
            elif user_input['dl'] == 'student_task':
                return self.download_student_task(course, user_input['username'], user_input['task'], include_old_submissions)
            elif user_input['dl'] == 'student':
                return self.download_student(course, user_input['username'], include_old_submissions)
            elif user_input['dl'] == 'group_task':
                return self.download_group_task(course, user_input['groupid'], user_input['task'], include_old_submissions)
            elif user_input['dl'] == 'group':
                return self.download_group(course, user_input['groupid'], include_old_submissions)
            elif user_input['dl'] == 'course':
                return self.download_course(course, user_input['groupby'], include_old_submissions)
            elif user_input['dl'] == 'task':
                return self.download_task(course, user_input['task'], include_old_submissions)
        else:
            raise web.notfound()

    def download_submission_set(self, submissions, filename, sub_folders):
        """ Create a tar archive with all the submissions """
        if len(submissions) == 0:
            raise web.notfound(renderer.notfound("There's no submission that matches your request"))
        try:
            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="' + filename + '"', unique=True)
            return get_submission_archive(submissions, sub_folders)
        except Exception as e:
            print e
            raise web.notfound()

    def download_course(self, course, groupby, include_old_submissions=False):
        """ Download all submissions for a course """
        submissions = list(get_database().submissions.find(
            {"courseid": course.get_id(), "username": {"$in": course.get_registered_users()}, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([course.get_id()]) + '.tgz', [groupby, 'taskid'])

    def download_task(self, course, taskid, include_old_submissions=False):
        """ Download all submission for a task """
        submissions = list(get_database().submissions.find(
            {"taskid": taskid, "courseid": course.get_id(), "username": {"$in": course.get_registered_users()},
             "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([course.get_id(), taskid]) + '.tgz', ['username'])

    def download_student(self, course, username, include_old_submissions=False):
        """ Download all submissions for a user for a given course """
        submissions = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([username, course.get_id()]) + '.tgz', ['taskid'])

    def download_group(self, course, groupid, include_old_submissions=False):
        """ Download all submissions for a group for a given course """
        submissions = list(get_database().submissions.find({"groupid": ObjectId(groupid), "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([groupid, course.get_id()]) + '.tgz', ['taskid'])

    def download_student_task(self, course, username, taskid, include_old_submissions=True):
        """ Download all submissions for a user for given task """
        submissions = list(get_database().submissions.find(
            {"username": username, "courseid": course.get_id(), "taskid": taskid, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([username, course.get_id(), taskid]) + '.tgz', [])

    def download_group_task(self, course, groupid, taskid, include_old_submissions=True):
        """ Download all submissions for a user for given task """
        submissions = list(get_database().submissions.find(
            {"groupid": ObjectId(groupid), "courseid": course.get_id(), "taskid": taskid, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([groupid, course.get_id(), taskid]) + '.tgz', [])

    def download_submission(self, subid, include_old_submissions=False):
        """ Download a specific submission """
        submissions = list(get_database().submissions.find({'_id': ObjectId(subid)}))
        if not include_old_submissions:
            submissions = self._keep_best_submission(submissions)
        return self.download_submission_set(submissions, subid + '.tgz', [])

    def _keep_best_submission(self, submissions):
        """ Internal command used to only keep the best submission, if any """
        submissions.sort(key=lambda item: item['submitted_on'], reverse=True)
        tasks = {}
        for sub in submissions:
            if sub["taskid"] not in tasks:
                tasks[sub["taskid"]] = {}
            for username in sub["username"]:
                if username not in tasks[sub["taskid"]]:
                    tasks[sub["taskid"]][username] = sub
                elif tasks[sub["taskid"]][username].get("grade", 0.0) < sub.get("grade", 0.0):
                    tasks[sub["taskid"]][username] = sub
        final_subs = []
        for task in tasks.itervalues():
            for sub in task.itervalues():
                final_subs.append(sub)
        return final_subs
