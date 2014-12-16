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
import StringIO
import base64
import json
import os.path
import tarfile
import tempfile
import time

from bson import json_util
from bson.objectid import ObjectId
import web

from frontend.base import get_database, get_gridfs
from frontend.base import renderer
from frontend.pages.course_admin.utils import get_course_and_check_rights
from frontend.submission_manager import get_input_from_submission


class DownloadSubmissionFiles(object):

    """ List informations about all tasks """

    def GET(self, courseid):
        """ GET request """
        course = get_course_and_check_rights(courseid)
        user_input = web.input()
        if "dl" in user_input:
            include_old_submissions = "include_all" in user_input

            if user_input['dl'] == 'submission':
                return self.download_submission(user_input['id'], include_old_submissions)
            elif user_input['dl'] == 'student_task':
                return self.download_student_task(course, user_input['username'], user_input['task'], include_old_submissions)
            elif user_input['dl'] == 'student':
                return self.download_student(course, user_input['username'], include_old_submissions)
            elif user_input['dl'] == 'course':
                return self.download_course(course, include_old_submissions)
            elif user_input['dl'] == 'task':
                return self.download_task(course, user_input['task'], include_old_submissions)
        else:
            raise web.notfound()

    def download_submission_set(self, submissions, filename, sub_folders):
        """ Create a tar archive with all the submissions """
        if len(submissions) == 0:
            raise web.notfound(renderer.notfound("There's no submission that matches your request"))
        try:
            tmpfile = tempfile.TemporaryFile()
            tar = tarfile.open(fileobj=tmpfile, mode='w:')

            for submission in submissions:
                submission = get_input_from_submission(submission)

                # Compute base path in the tar file
                base_path = "/"
                for sub_folder in sub_folders:
                    if sub_folder == 'taskid':
                        base_path = submission['taskid'] + '/' + base_path
                    elif sub_folder == 'username':
                        base_path = submission['username'] + '/' + base_path

                submission_json = StringIO.StringIO(json.dumps(submission, default=json_util.default, indent=4, separators=(',', ': ')))
                submission_json_fname = base_path + str(submission["_id"]) + '.test'
                info = tarfile.TarInfo(name=submission_json_fname)
                info.size = submission_json.len
                info.mtime = time.mktime(submission["submitted_on"].timetuple())

                # Add file in tar archive
                tar.addfile(info, fileobj=submission_json)

                # If there is an archive, add it too
                if 'archive' in submission and submission['archive'] is not None and submission['archive'] != "":
                    subfile = get_gridfs().get(submission['archive'])
                    taskfname = base_path + str(submission["_id"]) + '.tgz'

                    # Generate file info
                    info = tarfile.TarInfo(name=taskfname)
                    info.size = subfile.length
                    info.mtime = time.mktime(submission["submitted_on"].timetuple())

                    # Add file in tar archive
                    tar.addfile(info, fileobj=subfile)

                # If there files that were uploaded by the student, add them
                if submission['input'] is not None:
                    for pid, problem in submission['input'].iteritems():
                        # If problem is a dict, it is a file (from the specification of the problems)
                        if isinstance(problem, dict):
                            # Get the extension (match extensions with more than one dot too)
                            DOUBLE_EXTENSIONS = ['.tar.gz', '.tar.bz2', '.tar.bz', '.tar.xz']
                            if not problem['filename'].endswith(tuple(DOUBLE_EXTENSIONS)):
                                _, ext = os.path.splitext(problem['filename'])
                            else:
                                for t_ext in DOUBLE_EXTENSIONS:
                                    if problem['filename'].endswith(t_ext):
                                        ext = t_ext

                            subfile = StringIO.StringIO(base64.b64decode(problem['value']))
                            taskfname = base_path + str(submission["_id"]) + '_uploaded_files/' + pid + ext

                            # Generate file info
                            info = tarfile.TarInfo(name=taskfname)
                            info.size = subfile.len
                            info.mtime = time.mktime(submission["submitted_on"].timetuple())

                            # Add file in tar archive
                            tar.addfile(info, fileobj=subfile)

            # Close tarfile and put tempfile cursor at 0
            tar.close()
            tmpfile.seek(0)

            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="' + filename + '"', unique=True)
            return tmpfile
        except:
            raise web.notfound()

    def download_course(self, course, include_old_submissions=False):
        """ Download all submissions for a course """
        submissions = list(get_database().submissions.find({"courseid": course.get_id(), "username": {"$in": course.get_registered_users()}, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([course.get_id()]) + '.tgz', ['username', 'taskid'])

    def download_task(self, course, taskid, include_old_submissions=False):
        """ Download all submission for a task """
        submissions = list(get_database().submissions.find({"taskid": taskid, "courseid": course.get_id(), "username": {"$in": course.get_registered_users()}, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([course.get_id(), taskid]) + '.tgz', ['username'])

    def download_student(self, course, username, include_old_submissions=False):
        """ Download all submissions for a user for a given course """
        submissions = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([username, course.get_id()]) + '.tgz', ['taskid'])

    def download_student_task(self, course, username, taskid, include_old_submissions=True):
        """ Download all submissions for a user for given task """
        submissions = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "taskid": taskid, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([username, course.get_id(), taskid]) + '.tgz', [])

    def download_submission(self, subid, include_old_submissions=False):
        """ Download a specific submission """
        submissions = list(get_database().submissions.find({'_id': ObjectId(subid)}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, subid + '.tgz', [])

    def _keep_last_submission(self, submissions):
        """ Internal command used to only keep the last valid submission, if any """
        submissions.sort(key=lambda item: item['submitted_on'], reverse=True)
        tasks = {}
        for sub in submissions:
            if sub["taskid"] not in tasks:
                tasks[sub["taskid"]] = {}
            if sub["username"] not in tasks[sub["taskid"]]:
                tasks[sub["taskid"]][sub["username"]] = sub
            elif tasks[sub["taskid"]][sub["username"]].get("result", "") != "success" and sub.get("result", "") == "success":
                tasks[sub["taskid"]][sub["username"]] = sub
        print tasks
        final_subs = []
        for task in tasks.itervalues():
            for sub in task.itervalues():
                final_subs.append(sub)
        return final_subs
