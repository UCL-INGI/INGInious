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

from bson.objectid import ObjectId
import pymongo

from frontend.custom.courses import FrontendCourse
from frontend.backend_interface import get_job_manager
from frontend.base import get_database, get_gridfs
from frontend.parsable_text import ParsableText
from frontend.plugins.plugin_manager import PluginManager
import frontend.user as User
from frontend.user_data import UserData

import time
import os.path
import common.custom_yaml
import tarfile
import StringIO
import tempfile

def get_submission(submissionid, user_check=True):
    """ Get a submission from the database """
    sub = get_database().submissions.find_one({'_id': ObjectId(submissionid)})
    if user_check and not user_is_submission_owner(sub):
        return None
    return sub

def _job_done_callback(submissionid, task, job):
    """ Callback called by JobManager when a job is done. Updates the submission in the database with the data returned after the completion of the job """
    submission = get_submission(submissionid, False)
    submission = get_input_from_submission(submission)

    job = _parse_text(task, job)

    data = {
        "status": ("done" if job["result"] == "success" or job["result"] == "failed" else "error"),  # error only if error was made by INGInious
        "result": job["result"],
        "grade": job["grade"],
        "text": job.get("text", None),
        "tests": job.get("tests", None),
        "problems": (job["problems"] if "problems" in job else {}),
        "archive": (get_gridfs().put(base64.b64decode(job["archive"])) if "archive" in job else None)
    }

    # Store additional data
    dont_dump = ["task", "course", "input"]
    for index in job:
        if index not in data and index not in dont_dump:
            data[index] = job[index]

    # Save submission to database
    get_database().submissions.update(
        {"_id": submission["_id"]},
        {"$set": data}
    )

    for username in submission["username"]:
        UserData(username).update_stats(submission, job)

    PluginManager.get_instance().call_hook("submission_done", submission=submission, job=job)


def add_job(task, inputdata, debug=False):
    """ Add a job in the queue and returns a submission id.
        task is a Task instance and inputdata is the input as a dictionary
        If debug is true, more debug data will be saved
    """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to submit an object")

    username = User.get_username()
    course = FrontendCourse(task.get_course_id())

    obj = {
        "courseid": task.get_course_id(),
        "taskid": task.get_id(),
        "input": get_gridfs().put(
            json.dumps(inputdata)),
        "status": "waiting",
        "submitted_on": datetime.now()}

    if course.is_group_course() and username not in course.get_staff(True):
        group = get_database().groups.find_one({"course_id": task.get_course_id(), "users": username})
        obj.update({"username": group["users"], "groupid": group["_id"]})
    else:
        obj.update({"username": [username]})

    submissionid = get_database().submissions.insert(obj)

    PluginManager.get_instance().call_hook("new_submission", submissionid=submissionid, submission=obj, inputdata=inputdata)

    get_job_manager().new_job(task, inputdata, (lambda job: _job_done_callback(submissionid, task, job)), "Frontend - {}".format(username), debug)

    return submissionid


def get_input_from_submission(submission, only_input=False):
    """ Get the input of a submission. If only_input is False, returns the full submissions with a dictionnary object at the key "input". Else, returns only the dictionnary. """
    if isinstance(submission.get("input", {}), dict):
        if only_input:
            return submission.get("input", {})
        else:
            return submission
    else:
        inp = json.load(get_gridfs().get(submission['input']))
        if only_input:
            return inp
        else:
            submission["input"] = inp
            return submission


def is_running(submissionid, user_check=True):
    """ Tells if a submission is running/in queue """
    submission = get_submission(submissionid, user_check)
    return submission["status"] == "waiting"


def is_done(submissionid, user_check=True):
    """ Tells if a submission is done and its result is available """
    submission = get_submission(submissionid, user_check)
    return submission["status"] == "done" or submission["status"] == "error"


def user_is_submission_owner(submission):
    """ Returns true if the current user is the owner of this jobid, false else """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to verify if he owns a jobid")

    return User.get_username() in submission["username"]

def get_user_submissions(task):
    """ Get all the user's submissions for a given task """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to get his submissions")

    course = FrontendCourse(task.get_course_id())

    cursor = get_database().submissions.find({"username": User.get_username(), "taskid": task.get_id(), "courseid": task.get_course_id()})
    cursor.sort([("submitted_on", -1)])
    return list(cursor)


def get_user_last_submissions(query, limit, one_per_task=False):
    """ Get last submissions of a user """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to get his submissions")
    request = query.copy()
    request.update({"username": User.get_username()})

    # We only want the last x task tried, modify the request
    if one_per_task is True:
        data = get_database().submissions.aggregate([
            {"$match": request},
            {"$sort": {"submitted_on": pymongo.DESCENDING}},
            {"$group": {"_id": {"courseid": "$courseid", "taskid": "$taskid"}, "orig_id": {"$first": "$_id"},
                        "submitted_on": {"$first": "$submitted_on"}}},
            {"$sort": {"submitted_on": pymongo.DESCENDING}},
            {"$limit": limit}
        ])
        request = {"_id": {"$in": [d["orig_id"] for d in list(data)]}}

    cursor = get_database().submissions.find(request)
    cursor.sort([("submitted_on", -1)]).limit(limit)
    return list(cursor)


def _parse_text(task, job_result):
    """ Parses text """
    if "text" in job_result:
        job_result["text"] = ParsableText(job_result["text"], task.get_response_type()).parse()
    if "problems" in job_result:
        for problem in job_result["problems"]:
            job_result["problems"][problem] = ParsableText(job_result["problems"][problem], task.get_response_type()).parse()
    return job_result

def get_submission_archive(submissions, sub_folders):
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
        submission = get_input_from_submission(submission)

        # Compute base path in the tar file
        base_path = "/"
        for sub_folder in sub_folders:
            if sub_folder == 'taskid':
                base_path = submission['taskid'] + '/' + base_path
            elif sub_folder == 'username':
                base_path = submission['username'] + '/' + base_path

        submission_yaml = StringIO.StringIO(common.custom_yaml.dump(submission).encode('utf-8'))
        submission_yaml_fname = base_path + str(submission["_id"]) + '.test'
        info = tarfile.TarInfo(name=submission_yaml_fname)
        info.size = submission_yaml.len
        info.mtime = time.mktime(submission["submitted_on"].timetuple())

        # Add file in tar archive
        tar.addfile(info, fileobj=submission_yaml)

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
    return tmpfile