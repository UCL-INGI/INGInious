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
""" Manages submissions """
import base64
from datetime import datetime
import json
import time
import os.path
import tarfile
import StringIO
import tempfile

from bson.objectid import ObjectId
import pymongo

from inginious.frontend.common.parsable_text import ParsableText
import inginious.common.custom_yaml


class SubmissionManager(object):
    """ Manages submissions. Communicates with the database and the job manager. """

    def __init__(self, job_manager, user_manager, database, gridfs, hook_manager):
        """
        :type job_manager: inginious.backend.job_managers.abstract.AbstractJobManager
        :type user_manager: inginious.frontend.common.user_manager.AbstractUserManager
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type hook_manager: inginious.common.hook_manager.HookManager
        :return:
        """
        self._job_manager = job_manager
        self._user_manager = user_manager
        self._database = database
        self._gridfs = gridfs
        self._hook_manager = hook_manager

    def get_submission(self, submissionid, user_check=True):
        """ Get a submission from the database """
        sub = self._database.submissions.find_one({'_id': ObjectId(submissionid)})
        if user_check and not self.user_is_submission_owner(sub):
            return None
        return sub

    def _job_done_callback(self, submissionid, task, job):
        """ Callback called by JobManager when a job is done. Updates the submission in the database with the data returned after the completion of the job """
        submission = self.get_submission(submissionid, False)
        submission = self.get_input_from_submission(submission)

        data = {
            "status": ("done" if job["result"] == "success" or job["result"] == "failed" else "error"),  # error only if error was made by INGInious
            "result": job["result"],
            "grade": job["grade"],
            "text": job.get("text", None),
            "tests": job.get("tests", None),
            "problems": (job["problems"] if "problems" in job else {}),
            "archive": (self._gridfs.put(base64.b64decode(job["archive"])) if "archive" in job else None),
            "response_type": task.get_response_type()
        }

        # Store additional data
        dont_dump = ["task", "course", "input"]
        for index in job:
            if index not in data and index not in dont_dump:
                data[index] = job[index]

        # Save submission to database
        self._database.submissions.update(
            {"_id": submission["_id"]},
            {"$set": data}
        )

        self._hook_manager.call_hook("submission_done", submission=submission, job=job)

    def add_job(self, task, inputdata, debug=False):
        """
        Add a job in the queue and returns a submission id.
        :param task:  Task instance
        :type task: inginious.frontend.common.tasks.FrontendTask
        :param inputdata: the input as a dictionary
        :type inputdata: dict
        :param debug: If debug is true, more debug data will be saved
        :type debug: bool
        :return:
        """
        if not self._user_manager.session_logged_in():
            raise Exception("A user must be logged in to submit an object")

        username = self._user_manager.session_username()

        obj = {
            "courseid": task.get_course_id(),
            "taskid": task.get_id(),
            "input": self._gridfs.put(json.dumps(inputdata)),
            "status": "waiting",
            "submitted_on": datetime.now(),
            "username": [username]
        }

        submissionid = self._database.submissions.insert(obj)

        self._hook_manager.call_hook("new_submission", submissionid=submissionid, submission=obj, inputdata=inputdata)

        self._job_manager.new_job(task, inputdata, (lambda job: self._job_done_callback(submissionid, task, job)), "Frontend - {}".format(username),
                                  debug)

        return submissionid

    def get_input_from_submission(self, submission, only_input=False):
        """
            Get the input of a submission. If only_input is False, returns the full submissions with a dictionnary object at the key "input".
            Else, returns only the dictionnary.
        """
        if isinstance(submission.get("input", {}), dict):
            if only_input:
                return submission.get("input", {})
            else:
                return submission
        else:
            inp = json.load(self._gridfs.get(submission['input']))
            if only_input:
                return inp
            else:
                submission["input"] = inp
                return submission

    def get_feedback_from_submission(self, submission, only_feedback=False):
        """
            Get the input of a submission. If only_input is False, returns the full submissions with a dictionnary object at the key "input".
            Else, returns only the dictionnary.
        """
        if only_feedback:
            submission = {"text": submission.get("text", None), "problems": dict(submission.get("problems", {}))}
        if "text" in submission:
            submission["text"] = ParsableText(submission["text"], submission["response_type"]).parse()
        if "problems" in submission:
            for problem in submission["problems"]:
                submission["problems"][problem] = ParsableText(submission["problems"][problem], submission["response_type"]).parse()
        return submission

    def is_running(self, submissionid, user_check=True):
        """ Tells if a submission is running/in queue """
        submission = self.get_submission(submissionid, user_check)
        return submission["status"] == "waiting"

    def is_done(self, submissionid, user_check=True):
        """ Tells if a submission is done and its result is available """
        submission = self.get_submission(submissionid, user_check)
        return submission["status"] == "done" or submission["status"] == "error"

    def user_is_submission_owner(self, submission):
        """ Returns true if the current user is the owner of this jobid, false else """
        if not self._user_manager.session_logged_in():
            raise Exception("A user must be logged in to verify if he owns a jobid")

        return self._user_manager.session_username() in submission["username"]

    def get_user_submissions(self, task):
        """ Get all the user's submissions for a given task """
        if not self._user_manager.session_logged_in():
            raise Exception("A user must be logged in to get his submissions")

        cursor = self._database.submissions.find({"username": self._user_manager.session_username(),
                                                  "taskid": task.get_id(), "courseid": task.get_course_id()})
        cursor.sort([("submitted_on", -1)])
        return list(cursor)

    def get_user_last_submissions(self, query, limit, one_per_task=False):
        """ Get last submissions of a user """
        if not self._user_manager.session_logged_in():
            raise Exception("A user must be logged in to get his submissions")
        request = query.copy()
        request.update({"username": self._user_manager.session_username()})

        # We only want the last x task tried, modify the request
        if one_per_task is True:
            data = self._database.submissions.aggregate([
                {"$match": request},
                {"$sort": {"submitted_on": pymongo.DESCENDING}},
                {"$group": {"_id": {"courseid": "$courseid", "taskid": "$taskid"}, "orig_id": {"$first": "$_id"},
                            "submitted_on": {"$first": "$submitted_on"}}},
                {"$sort": {"submitted_on": pymongo.DESCENDING}},
                {"$limit": limit}
            ])
            request = {"_id": {"$in": [d["orig_id"] for d in list(data)]}}

        cursor = self._database.submissions.find(request)
        cursor.sort([("submitted_on", -1)]).limit(limit)
        return list(cursor)

    def get_user_last_submissions_for_course(self, course, limit=5, one_per_task=False):
        """ Returns a given number (default 5) of submissions of task from the course given"""
        return self.get_user_last_submissions({"courseid": course.get_id(), "taskid": {"$in": course.get_tasks().keys()}}, limit, one_per_task)

    @classmethod
    def keep_best_submission(cls, submissions):
        """ Command used to only keep the best submission, if any """
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

    def get_submission_archive(self, submissions, sub_folders, classrooms):
        """
        :param submissions: a list of submissions
        :param sub_folders: possible values:
            []: put all submissions in /
            ['taskid']: put all submissions for each task in a different directory /taskid/
            ['username']: put all submissions for each user in a different directory /username/
            ['taskid','username']: /taskid/username/
            ['username','taskid']: /username/taskid/
        :return: a file-like object containing a tgz archive of all the submissions
        """
        tmpfile = tempfile.TemporaryFile()
        tar = tarfile.open(fileobj=tmpfile, mode='w:gz')

        for submission in submissions:
            submission = self.get_input_from_submission(submission)

            # Considering multiple single submissions for each user
            for username in submission["username"]:
                # Compute base path in the tar file
                base_path = "/"
                for sub_folder in sub_folders:
                    if sub_folder == 'taskid':
                        base_path = submission['taskid'] + base_path
                    elif sub_folder == 'username':
                        base_path = '_' + '-'.join(submission['username']) + base_path
                        base_path = base_path[1:]
                    elif sub_folder == 'classroom':
                        base_path = (classrooms[username]["description"] + " (" + str(classrooms[username]["_id"]) + ")").replace(" ", "_") + base_path

                    base_path = '/' + base_path
                base_path = base_path[1:]

                submission_yaml = StringIO.StringIO(inginious.common.custom_yaml.dump(submission).encode('utf-8'))
                submission_yaml_fname = base_path + str(submission["_id"]) + '/submission.test'

                # Avoid putting two times the same submission on the same place
                if submission_yaml_fname not in tar.getnames():

                    info = tarfile.TarInfo(name=submission_yaml_fname)
                    info.size = submission_yaml.len
                    info.mtime = time.mktime(submission["submitted_on"].timetuple())

                    # Add file in tar archive
                    tar.addfile(info, fileobj=submission_yaml)

                    # If there is an archive, add it too
                    if 'archive' in submission and submission['archive'] is not None and submission['archive'] != "":
                        subfile = self._gridfs.get(submission['archive'])
                        subtar = tarfile.open(fileobj=subfile, mode="r:gz")

                        for member in subtar.getmembers():
                            subtarfile = subtar.extractfile(member)
                            member.name = base_path + str(submission["_id"]) + "/archive/" + member.name
                            tar.addfile(member, subtarfile)

                        subtar.close()
                        subfile.close()

                    # If there files that were uploaded by the student, add them
                    if submission['input'] is not None:
                        for pid, problem in submission['input'].iteritems():
                            # If problem is a dict, it is a file (from the specification of the problems)
                            if isinstance(problem, dict):
                                # Get the extension (match extensions with more than one dot too)
                                DOUBLE_EXTENSIONS = ['.tar.gz', '.tar.bz2', '.tar.bz', '.tar.xz']
                                ext = ""
                                if not problem['filename'].endswith(tuple(DOUBLE_EXTENSIONS)):
                                    _, ext = os.path.splitext(problem['filename'])
                                else:
                                    for t_ext in DOUBLE_EXTENSIONS:
                                        if problem['filename'].endswith(t_ext):
                                            ext = t_ext

                                subfile = StringIO.StringIO(base64.b64decode(problem['value']))
                                taskfname = base_path + str(submission["_id"]) + '/uploaded_files/' + pid + ext

                                # Generate file info
                                info = tarfile.TarInfo(name=taskfname)
                                info.size = subfile.len
                                info.mtime = time.mktime(submission["submitted_on"].timetuple())

                                # Add file in tar archive
                                tar.addfile(info, fileobj=subfile)

        # Close tarfile and put tempfile cursor at 0
        tar.close()
        tmpfile.seek(0)
        return tmpfile
