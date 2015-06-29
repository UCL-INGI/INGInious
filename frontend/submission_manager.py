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

from backend.job_managers.local import LocalJobManager
from backend.job_managers.remote_docker import RemoteDockerJobManager
from backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from common.courses import Course
from frontend.base import get_database, get_gridfs
from frontend.configuration import INGIniousConfiguration
from frontend.parsable_text import ParsableText
from frontend.plugins.plugin_manager import PluginManager
import frontend.user as User
from frontend.user_data import UserData

job_managers = []


def get_job_manager():
    """ Get the JobManager. Should only be used by very specific plugins """
    return get_job_manager.job_manager


def init_backend_interface(plugin_manager):
    """ inits everything that makes the backend working """

    # Updates the submissions that have a jobid with the status error, as the server restarted """
    get_database().submissions.update({'jobid': {"$exists": True}},
                                      {"$unset": {'jobid': ""},
                                       "$set": {'status': 'error', 'grade': 0.0, 'text': 'Internal error. Server restarted'}}, multi=True)

    # Create the job manager
    backend_type = INGIniousConfiguration.get("backend", "local")
    if backend_type == "local":
        get_job_manager.job_manager = LocalJobManager(
            INGIniousConfiguration.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
            INGIniousConfiguration.get('local_agent_tmp_dir', "/tmp/inginious_agent"), plugin_manager)
    elif backend_type == "remote":
        get_job_manager.job_manager = RemoteDockerJobManager(INGIniousConfiguration.get("docker_daemons", []),
                                                             INGIniousConfiguration.get('containers', {"default": "ingi/inginious-c-default",
                                                                                                       "sekexe": "ingi/inginious-c-sekexe"}),
                                                             plugin_manager)
    elif backend_type == "remote_manual":
        get_job_manager.job_manager = RemoteManualAgentJobManager(
            INGIniousConfiguration.get("agents", [{"host": "localhost", "port": 5001}]),
            INGIniousConfiguration.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
            plugin_manager)
    else:
        raise Exception("Unknown backend {}".format(backend_type))


def start_backend_interface():
    """ Starts the backend interface. Should be called after the initialisation of the plugin manager. """
    get_job_manager().start()


def get_submission(submissionid, user_check=True):
    """ Get a submission from the database """
    sub = get_database().submissions.find_one({'_id': ObjectId(submissionid)})
    if user_check and not user_is_submission_owner(sub):
        return None
    return sub


def get_submission_from_jobid(jobid):
    """ Get a waiting submission from its jobid """
    return get_database().submissions.find_one({'jobid': jobid})


def job_done_callback(jobid, task, job):
    """ Callback called by JobManager when a job is done. Updates the submission in the database with the data returned after the completion of the job """
    submission = get_submission_from_jobid(jobid)
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
        {
            "$unset": {"jobid": ""},
            "$set": data
        }
    )

    if "group" in submission:
        group = get_database().groups.find_one({"_id": submission["group"]})
        for username in group["users"]:
            UserData(username).update_stats(submission, job)
    else:
        UserData(submission["username"]).update_stats(submission, job)

    PluginManager.get_instance().call_hook("submission_done", submission=submission, job=job)


def add_job(task, inputdata, debug=False):
    """ Add a job in the queue and returns a submission id.
        task is a Task instance and inputdata is the input as a dictionary
        If debug is true, more debug data will be saved
    """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to submit an object")

    username = User.get_username()

    jobid = get_job_manager().new_job_id()

    obj = {
        "courseid": task.get_course_id(),
        "taskid": task.get_id(),
        "input": get_gridfs().put(
            json.dumps(inputdata)),
        "status": "waiting",
        "jobid": jobid,
        "submitted_on": datetime.now()}

    if Course.get_course_descriptor_content(task.get_course_id()).get("groups", False):
        group = get_database().groups.find_one({"course_id": task.get_course_id(), "users": username})
        obj.update({"group": group["_id"]})
    else:
        obj.update({"username": username})

    submissionid = get_database().submissions.insert(obj)

    PluginManager.get_instance().call_hook("new_submission", submissionid=submissionid, submission=obj, jobid=jobid, inputdata=inputdata)

    get_job_manager().new_job(task, inputdata, job_done_callback, "Frontend - {}".format(username), jobid, debug)

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

    if "group" in submission:
        return get_database().groups.find({"_id": submission["group"], "users": User.get_username()}).count() > 0
    else:
        return submission["username"] == User.get_username()


def get_user_submissions(task):
    """ Get all the user's submissions for a given task """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to get his submissions")

    if Course.get_course_descriptor_content(task.get_course_id()).get("groups", False):
        group = get_database().groups.find_one({"course_id": task.get_course_id(), "users": User.get_username()})
        cursor = get_database().submissions.find({"group": group["_id"], "taskid": task.get_id(), "courseid": task.get_course_id()})
    else:
        cursor = get_database().submissions.find({"username": User.get_username(), "taskid": task.get_id(), "courseid": task.get_course_id()})
    cursor.sort([("submitted_on", -1)])
    return list(cursor)


def get_user_last_submissions(query, limit, one_per_task=False):
    """ Get last submissions of a user """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to get his submissions")
    request = query.copy()
    request.update({"$or": [
        {"username": User.get_username()},
        {"group": {"$in": [g["_id"] for g in get_database().groups.find({"users": User.get_username()})]}}]})

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
