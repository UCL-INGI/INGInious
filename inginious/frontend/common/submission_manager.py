# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages submissions """
from abc import ABCMeta
import json
import time
import os.path
import tarfile
import io
import tempfile

import bson
import web
from datetime import datetime

from bson.objectid import ObjectId
import pymongo
from pymongo.collection import ReturnDocument

from inginious.frontend.common.parsable_text import ParsableText
import inginious.common.custom_yaml

from inginious.client.client_sync import ClientSync


class SubmissionManager(object, metaclass=ABCMeta):
    """ Manages submissions. Communicates with the database and to the backend/agent using a Client. """

    def __init__(self, client, user_manager, database, gridfs, hook_manager):
        """
        :type client: inginious.client.client.AbstractClient
        :type user_manager: inginious.frontend.common.user_manager.AbstractUserManager
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type hook_manager: inginious.common.hook_manager.HookManager
        :return:
        """
        self._client = client
        self._user_manager = user_manager
        self._database = database
        self._gridfs = gridfs
        self._hook_manager = hook_manager
        self._logger = None

    def get_available_environments(self):
        """:return a list of available environments """
        return self._client.get_available_containers()

    def get_submission(self, submissionid, user_check=True):
        """ Get a submission from the database """
        sub = self._database.submissions.find_one({'_id': ObjectId(submissionid)})
        if user_check and not self.user_is_submission_owner(sub):
            return None
        return sub

    def _job_done_callback(self, submissionid, task, result, grade, problems,
                           tests, custom, archive, stdout, stderr, newsub=True):  # pylint: disable=unused-argument
        """ Callback called by Client when a job is done. Updates the submission in the database with the data returned after the completion of the
        job """
        submission = self.get_submission(submissionid, False)
        submission = self.get_input_from_submission(submission)

        data = {
            "status": ("done" if result[0] == "success" or result[0] == "failed" else "error"),  # error only if error was made by INGInious
            "result": result[0],
            "grade": grade,
            "text": result[1],
            "tests": tests,
            "problems": problems,
            "archive": (self._gridfs.put(archive) if archive is not None else None),
            "custom": custom,
            "stdout": stdout,
            "stderr": stderr
        }

        # Save submission to database
        submission = self._database.submissions.find_one_and_update(
            {"_id": submission["_id"]},
            {"$set": data, "$unset": {'jobid': ""}},
            return_document=ReturnDocument.AFTER
        )

        self._hook_manager.call_hook("submission_done", submission=submission, archive=archive, newsub=newsub)

    def add_unsaved_job(self, task, inputdata):
        temp_client = ClientSync(self._client)
        return temp_client.new_job(task, inputdata)

    def add_job(self, task, inputdata, debug=False):
        """
        Add a job in the queue and returns a submission id.
        :param task:  Task instance
        :type task: inginious.frontend.common.tasks.FrontendTask
        :param inputdata: the input as a dictionary
        :type inputdata: dict
        :param debug: If debug is true, more debug data will be saved
        :type debug: bool
        :returns: the new submission id and the removed submission id
        """
        if not self._user_manager.session_logged_in():
            raise Exception("A user must be logged in to submit an object")

        username = self._user_manager.session_username()

        # Prevent student from submitting several submissions together
        waiting_submission = self._database.submissions.find_one({
            "courseid": task.get_course_id(),
            "taskid": task.get_id(),
            "username": username,
            "status": "waiting"})

        if waiting_submission is not None:
            raise Exception("A submission is already pending for this task!")

        obj = {
            "courseid": task.get_course_id(),
            "taskid": task.get_id(),
            "input": self._gridfs.put(bson.BSON.encode(inputdata)),
            "status": "waiting",
            "submitted_on": datetime.now(),
            "username": [username],
            "response_type": task.get_response_type()
        }

        self._before_submission_insertion(task, inputdata, debug, obj)

        submissionid = self._database.submissions.insert(obj)

        # Send additional data to the client in inputdata. For now, the username and the language. New fields can be added with the
        # new_submission hook
        inputdata["@username"] = username
        inputdata["@lang"] = "en_US"  # TODO

        to_remove = self._after_submission_insertion(task, inputdata, debug, obj, submissionid)

        self._hook_manager.call_hook("new_submission", submissionid=submissionid, submission=obj, inputdata=inputdata)

        ssh_callback = lambda host, port, password: None
        if debug == "ssh":
            ssh_callback = lambda host, port, password: self._handle_ssh_callback(submissionid, host, port, password)

        jobid = self._client.new_job(task, inputdata,
                                     (lambda result, grade, problems, tests, custom, archive, stdout, stderr:
                                      self._job_done_callback(submissionid, task, result, grade, problems, tests, custom, archive, stdout, stderr, True)),
                                     "Frontend - {}".format(username), debug, ssh_callback)

        self._database.submissions.update(
            {"_id": submissionid, "status": "waiting"},
            {"$set": {"jobid": jobid}}
        )

        self._logger.info("New submission from %s - %s - %s/%s - %s", self._user_manager.session_username(),
                          self._user_manager.session_email(), task.get_course_id(), task.get_id(),
                          web.ctx['ip'])

        return submissionid, to_remove

    def _before_submission_insertion(self, task, inputdata, debug, obj):
        """
        Called before any new submission is inserted into the database. Allows you to modify obj, the new document that will be inserted into the
        database. Should be overridden in subclasses.

        :param task: Task related to the submission
        :param inputdata: input of the student
        :param debug: True, False or "ssh". See add_job.
        :param obj: the new document that will be inserted
        """
        pass

    def _after_submission_insertion(self, task, inputdata, debug, submission, submissionid):
        """
        Called after any new submission is inserted into the database, but before starting the job.  Should be overridden in subclasses.
        :param task: Task related to the submission
        :param inputdata: input of the student
        :param debug: True, False or "ssh". See add_job.
        :param submission: the new document that was inserted (do not contain _id)
        :param submissionid: submission id of the submission
        """
        pass

    def _always_keep_best(self):
        """  Indicates if the best submissions are always kept in all cases (LTI) """
        return False

    def _delete_exceeding_submissions(self, username, task, max_submissions_bound=-1):
        """ Deletes exceeding submissions from the database, to keep the database relatively small """

        if max_submissions_bound <= 0:
            max_submissions = task.get_stored_submissions()
        elif task.get_stored_submissions() <= 0:
            max_submissions = max_submissions_bound
        else:
            max_submissions = min(max_submissions_bound, task.get_stored_submissions())

        if max_submissions <= 0:
            return []
        tasks = list(self._database.submissions.find(
            {"username": username, "courseid": task.get_course_id(), "taskid": task.get_id()},
            projection=["_id", "status", "result", "grade", "submitted_on"],
            sort=[('submitted_on', pymongo.ASCENDING)]))

        # List the entries to keep
        to_keep = set([])

        if task.get_evaluate() == 'best' or self._always_keep_best():
            # Find the best "status"="done" and "result"="success"
            idx_best = -1
            for idx, val in enumerate(tasks):
                if val["status"] == "done":
                    if idx_best == -1 or tasks[idx_best]["grade"] < val["grade"]:
                        idx_best = idx

            # Always keep the best submission
            if idx_best != -1:
                to_keep.add(tasks[idx_best]["_id"])
        elif task.get_evaluate() == 'student':
            user_task = self._database.user_tasks.find_one({
                "courseid": task.get_course_id(),
                "taskid": task.get_id(),
                "username": username
            })

            submissionid = user_task.get('submissionid', None)
            if submissionid:
                to_keep.add(submissionid)

        # Always keep running submissions
        for val in tasks:
            if val["status"] == "waiting":
                to_keep.add(val["_id"])

        while len(to_keep) < max_submissions and len(tasks) > 0:
            to_keep.add(tasks.pop()["_id"])

        to_delete = {val["_id"] for val in tasks}.difference(to_keep)
        self._database.submissions.delete_many({"_id": {"$in": list(to_delete)}})

        return list(map(str, to_delete))

    def get_input_from_submission(self, submission, only_input=False):
        """
            Get the input of a submission. If only_input is False, returns the full submissions with a dictionnary object at the key "input".
            Else, returns only the dictionnary.
        """
        inp = bson.BSON.decode(self._gridfs.get(submission['input']).read())
        if only_input:
            return inp
        else:
            submission["input"] = inp
            return submission

    def get_feedback_from_submission(self, submission, only_feedback=False, show_everything=False):
        """
            Get the input of a submission. If only_input is False, returns the full submissions with a dictionnary object at the key "input".
            Else, returns only the dictionnary.

            If show_everything is True, feedback normally hidden is shown.
        """
        if only_feedback:
            submission = {"text": submission.get("text", None), "problems": dict(submission.get("problems", {}))}
        if "text" in submission:
            submission["text"] = ParsableText(submission["text"], submission["response_type"], show_everything).parse()
        if "problems" in submission:
            for problem in submission["problems"]:
                if isinstance(submission["problems"][problem], str):  # fallback for old-style submissions
                    submission["problems"][problem] = (submission.get('result', 'crash'), ParsableText(submission["problems"][problem],
                                                                                                       submission["response_type"],
                                                                                                       show_everything).parse())
                else:  # new-style submission
                    submission["problems"][problem] = (submission["problems"][problem][0], ParsableText(submission["problems"][problem][1],
                                                                                                        submission["response_type"],
                                                                                                        show_everything).parse())
        return submission

    def is_running(self, submissionid, user_check=True):
        """ Tells if a submission is running/in queue """
        submission = self.get_submission(submissionid, user_check)
        return submission["status"] == "waiting"

    def is_done(self, submissionid_or_submission, user_check=True):
        """ Tells if a submission is done and its result is available """
        # TODO: not a very nice way to avoid too many database call. Should be refactored.
        if isinstance(submissionid_or_submission, dict):
            submission = submissionid_or_submission
        else:
            submission = self.get_submission(submissionid_or_submission, False)
        if user_check and not self.user_is_submission_owner(submission):
            return None
        return submission["status"] == "done" or submission["status"] == "error"

    def kill_running_submission(self, submissionid, user_check=True):
        """ Attempt to kill the remote job associated with this submission id.
        :param submissionid:
        :param user_check: Check if the current user owns this submission
        :return: True if the job was killed, False if an error occurred
        """
        submission = self.get_submission(submissionid, user_check)
        if not submission:
            return False
        if "jobid" not in submission:
            return False
        return self._client.kill_job(submission["jobid"])

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

    def get_user_last_submissions(self, limit=5, request=None):
        """ Get last submissions of a user """
        if request is None:
            request = {}

        request.update({"username": self._user_manager.session_username()})

        # Before, submissions were first sorted by submission date, then grouped
        # and then resorted by submission date before limiting. Actually, grouping
        # and pushing, keeping the max date, followed by result filtering is much more
        # efficient
        data = self._database.submissions.aggregate([
            {"$match": request},
            {"$group": {"_id": {"courseid": "$courseid", "taskid": "$taskid"},
                        "submitted_on": {"$max": "$submitted_on"},
                        "submissions": {"$push": {
                            "_id": "$_id",
                            "result": "$result",
                            "status" : "$status",
                            "courseid": "$courseid",
                            "taskid": "$taskid",
                            "submitted_on": "$submitted_on"
                        }},
            }},
            {"$project": {
                "submitted_on": 1,
                "submissions": {
                    # This could be replaced by $filter if mongo v3.2 is set as dependency
                    "$setDifference": [
                        {"$map": {
                            "input": "$submissions",
                            "as": "submission",
                            "in": {
                                "$cond": [{"$eq": ["$submitted_on", "$$submission.submitted_on"]}, "$$submission", False]
                            }
                        }},
                        [False]
                    ]
                }
            }},
            {"$sort": {"submitted_on": pymongo.DESCENDING}},
            {"$limit": limit}
        ])

        return [item["submissions"][0] for item in data]

    def get_gridfs(self):
        """ Returns the GridFS used by the submission manager """
        return self._gridfs

    def get_submission_archive(self, submissions, sub_folders, aggregations, archive_file=None):
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
        tmpfile = archive_file if archive_file is not None else tempfile.TemporaryFile()
        tar = tarfile.open(fileobj=tmpfile, mode='w:gz')

        for submission in submissions:
            submission = self.get_input_from_submission(submission)

            submission_yaml = io.BytesIO(inginious.common.custom_yaml.dump(submission).encode('utf-8'))

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
                    elif sub_folder == 'aggregation':
                        if aggregations[username] is None:
                            # If classrooms are not used, and user is not grouped, his classroom is replaced by None
                            base_path = '_' + '-'.join(submission['username']) + base_path
                            base_path = base_path[1:]
                        else:
                            base_path = (aggregations[username]["description"] +
                                         " (" + str(aggregations[username]["_id"]) + ")").replace(" ", "_") + base_path

                    base_path = '/' + base_path
                base_path = base_path[1:]

                submission_yaml_fname = base_path + str(submission["_id"]) + '/submission.test'

                # Avoid putting two times the same submission on the same place
                if submission_yaml_fname not in tar.getnames():

                    info = tarfile.TarInfo(name=submission_yaml_fname)
                    info.size = submission_yaml.getbuffer().nbytes
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
                        for pid, problem in submission['input'].items():
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

                                subfile = io.BytesIO(problem['value'])
                                taskfname = base_path + str(submission["_id"]) + '/uploaded_files/' + pid + ext

                                # Generate file info
                                info = tarfile.TarInfo(name=taskfname)
                                info.size = subfile.getbuffer().nbytes
                                info.mtime = time.mktime(submission["submitted_on"].timetuple())

                                # Add file in tar archive
                                tar.addfile(info, fileobj=subfile)

        # Close tarfile and put tempfile cursor at 0
        tar.close()
        tmpfile.seek(0)
        return tmpfile

    def _handle_ssh_callback(self, submission_id, host, port, password):
        """ Handles the creation of a remote ssh server """
        if host is not None:  # ignore late calls (a bit hacky, but...)
            obj = {
                "ssh_host": host,
                "ssh_port": port,
                "ssh_password": password
            }
            self._database.submissions.update_one({"_id": submission_id}, {"$set": obj})

    def get_job_queue_snapshot(self):
        """ Get a snapshot of the remote backend job queue. May be a cached version.
            May not contain recent jobs. May return None if no snapshot is available

        Return a tuple of two lists (None, None):
        jobs_running: a list of tuples in the form
            (job_id, is_current_client_job, info, launcher, started_at, max_end)
            where
            - job_id is a job id. It may be from another client.
            - is_current_client_job is a boolean indicating if the client that asked the request has started the job
            - agent_name is the agent name
            - info is "courseid/taskid"
            - launcher is the name of the launcher, which may be anything
            - started_at the time (in seconds since UNIX epoch) at which the job started
            - max_end the time at which the job will timeout (in seconds since UNIX epoch), or -1 if no timeout is set
        jobs_waiting: a list of tuples in the form
            (job_id, is_current_client_job, info, launcher, max_time)
            where
            - job_id is a job id. It may be from another client.
            - is_current_client_job is a boolean indicating if the client that asked the request has started the job
            - info is "courseid/taskid"
            - launcher is the name of the launcher, which may be anything
            - max_time the maximum time that can be used, or -1 if no timeout is set
        """
        return self._client.get_job_queue_snapshot()

    def get_job_queue_info(self, jobid):
        """
        :param jobid: the JOB id (not the submission id!). You should retrieve it before calling this function by calling get_submission(...)[
        "job_id"].
        :return: If the submission is in the queue, then returns a tuple (nb tasks before running (or -1 if running), approx wait time in seconds)
                 Else, returns None
        """
        return self._client.get_job_queue_info(jobid)


def update_pending_jobs(database):
    """ Updates pending jobs status in the database """

    # Updates the submissions that are waiting with the status error, as the server restarted
    database.submissions.update({'status': 'waiting'},
                                {"$unset": {'jobid': ""},
                                 "$set": {'status': 'error', 'grade': 0.0, 'text': 'Internal error. Server restarted'}}, multi=True)
