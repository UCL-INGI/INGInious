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
""" Manages batch containers """

import frontend.user as User
from frontend.backend_interface import get_job_manager
from frontend.configuration import INGIniousConfiguration
from frontend.base import get_database, get_gridfs
from frontend.submission_manager import get_submission_archive
import os
import tempfile
import tarfile
from datetime import datetime
from bson.objectid import ObjectId

def _get_course_data(course):
    """ Returns a file-like object to a tgz archive of the course files """
    dir_path = os.path.join(INGIniousConfiguration["tasks_directory"], course.get_id())
    tmpfile = tempfile.TemporaryFile()
    tar = tarfile.open(fileobj=tmpfile, mode='w:gz')
    tar.add(dir_path,"/",True)
    tar.close()
    tmpfile.seek(0)
    return tmpfile

def _get_submissions_data(course):
    """ Returns a file-like object to a tgz archive containing all the submissions made by the students for the course """
    submissions = list(get_database().submissions.find(
        {"courseid": course.get_id(), "username": {"$in": course.get_registered_users()}, "status": {"$in": ["done", "error"]}}))
    return get_submission_archive(submissions, ['username', 'taskid'])

def get_batch_container_metadata(container_name):
    """
        Returns the arguments needed by a particular batch container.
        :returns: a tuple in the form
            ("container title",
             "container description in restructuredtext",
             {"key":
                {
                 "type:" "file", #or "text",
                 "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                 "name": "name of the field", #not mandatory in file, default "key"
                 "description": "a short description of what this field is used for" #not mandatory, default ""
                }
             }
            )
    """
    if container_name not in INGIniousConfiguration.get("batch_containers", []):
        raise Exception("This batch container is not allowed to be started")

    return get_job_manager().get_batch_container_metadata(container_name)

def get_all_batch_containers_metadata():
    """
        Returns the arguments needed for all batch containers.
        :returns: a dict, containing as keys the container image names, and as value tuples in the form
            ("container title",
             "container description in restructuredtext",
             {"key":
                {
                 "type:" "file", #or "text",
                 "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                 "name": "name of the field", #not mandatory in file, default "key"
                 "description": "a short description of what this field is used for" #not mandatory, default ""
                }
             }
            )
    """
    return {container_name:get_batch_container_metadata(container_name) for container_name in INGIniousConfiguration.get("batch_containers", [])}

def add_batch_job(course, container_name, inputdata, launcher_name=None, skip_permission=False):
    """
        Add a job in the queue and returns a batch job id.
        inputdata is a dict containing all the keys of get_batch_container_metadata(container_name)[2] BUT the keys "course" and "submission" IF their
        type is "file". (the content of the course and the submission will be automatically included by this function.)
        The values associated are file-like objects for "file" types and  strings for "text" types.
    """

    if not skip_permission:
        if not User.is_logged_in():
            raise Exception("A user must be logged in to submit an object")

        username = User.get_username()
        launcher_name = launcher_name or username

        if username not in course.get_admins():
            raise Exception("The user must be an administrator to start a batch job")

    if container_name not in INGIniousConfiguration.get("batch_containers", []):
        raise Exception("This batch container is not allowed to be started")

    container_args = get_job_manager().get_batch_container_metadata(container_name)[2]
    if container_args is None:
        raise Exception("This batch container is not available")

    # Download the course content and submissions and add them to the input
    if "course" in container_args and container_args["course"]["type"] == "file" and "course" not in inputdata:
        inputdata["course"] = _get_course_data(course)
    if "submissions" in container_args and container_args["submissions"]["type"] == "file" and "submissions" not in inputdata:
        inputdata["submissions"] = _get_submissions_data(course)

    obj = {"courseid": course.get_id(), 'container_name': container_name, "submitted_on": datetime.now()}

    batch_job_id = get_database().batch_jobs.insert(obj)

    launcher_name = launcher_name or "plugin"

    get_job_manager().new_batch_job(container_name, inputdata, lambda r: _batch_job_done_callback(batch_job_id, r),
                                    launcher_name="Frontend - {}".format(launcher_name))

    return batch_job_id

def _batch_job_done_callback(batch_job_id, result):
    """ Called when the batch job with id jobid has finished.
        result is a dictionnary, containing:

        - {"retval": 0, "stdout": "...", "stderr": "...", "file": "..."}
            if everything went well.(where file is a tgz file containing the content of the / output folder from the container)
        - {"retval": "...", "stdout": "...", "stderr": "..."}
            if the container crashed (retval is an int != 0)
        - {"retval": -1, "stderr": "the error message"}
            if the container failed to start
    """

    # If there is a tgz file to save, put it in gridfs
    if "file" in result:
        result["file"] = get_gridfs().put(result["file"].read())

    # Save submission to database
    get_database().batch_jobs.update(
        {"_id": batch_job_id},
        {"$set": {"result": result}}
    )

def get_batch_job_status(batch_job_id):
    """ Returns the batch job with id batch_job_id Batch jobs are dicts in the form
        {"courseid": "...", "container_name": "..."} if the job is still ongoing, and
        {"courseid": "...", "container_name": "...", "results": {}} if the job is done.
        the dict result can be either:

        - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
            if everything went well. (file is an gridfs id to a tgz file)
        - {"retval":"...", "stdout": "...", "stderr":"..."}
            if the container crashed (retval is an int != 0)
        - {"retval":-1, "stderr": "the error message"}
            if the container failed to start
    """
    return get_database().batch_jobs.find_one({"_id": ObjectId(batch_job_id)})

def get_all_batch_jobs_for_course(course_id):
    """ Returns all the batch jobs for the course course id. Batch jobs are dicts in the form
        {"courseid": "...", "container_name": "...", "submitted_on":"..."} if the job is still ongoing, and
        {"courseid": "...", "container_name": "...", "submitted_on":"...", "results": {}} if the job is done.
        the dict result can be either:

        - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
            if everything went well. (file is an gridfs id to a tgz file)
        - {"retval":"...", "stdout": "...", "stderr":"..."}
            if the container crashed (retval is an int != 0)
        - {"retval":-1, "stderr": "the error message"}
            if the container failed to start
    """
    return list(get_database().batch_jobs.find({"courseid": course_id}))

def drop_batch_job(batch_job_id):
    """ Delete a **finished** batch job from the database """
    job = get_database().batch_jobs.find_one({"_id": ObjectId(batch_job_id)})
    if "result" not in job:
        raise Exception("Batch job is still running, cannot delete it")
    get_database().batch_jobs.remove({"_id": ObjectId(batch_job_id)})
    if "file" in job["result"]:
        get_gridfs().delete(job["result"]["file"])