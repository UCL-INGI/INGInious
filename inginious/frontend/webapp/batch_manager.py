# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages batch containers """
import logging
import os
import tempfile
import tarfile
from datetime import datetime

from bson.objectid import ObjectId
import web


class BatchManager(object):
    """
        Manages batch jobs. Store them in DB and communicates with the inginious.backend to start them.
    """

    def __init__(self, client, database, gridfs, submission_manager, user_manager, task_directory):
        self._client = client
        self._database = database
        self._gridfs = gridfs
        self._submission_manager = submission_manager
        self._user_manager = user_manager
        self._task_directory = task_directory
        self._logger = logging.getLogger("inginious.batch")

    def _get_course_data(self, course):
        """ Returns a file-like object to a tgz archive of the course files """
        dir_path = os.path.join(self._task_directory, course.get_id())
        tmpfile = tempfile.TemporaryFile()
        tar = tarfile.open(fileobj=tmpfile, mode='w:gz')
        tar.add(dir_path, "/", True)
        tar.close()
        tmpfile.seek(0)
        return tmpfile

    def _get_submissions_data(self, course, tasks, folders, best_only):
        """ Returns a file-like object to a tgz archive containing all the submissions made by the students for the course """
        users = self._user_manager.get_course_registered_users(course)

        db_args = {"courseid": course.get_id(), "username": {"$in": users}, "status": {"$in": ["done", "error"]}}
        if tasks is not None:
            db_args["taskid"] = {"$in": tasks}
        submissions = list(self._database.submissions.find(db_args))
        if best_only != "0":
            submissions = self._submission_manager.keep_best_submission(submissions)
        return self._submission_manager.get_submission_archive(submissions, list(reversed(folders.split('/'))), {})

    def get_batch_container_metadata(self, container_name):
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
                     "description": "a short description of what this field is used for", #not mandatory, default ""
                     "custom_key1": "custom_value1",
                     ...
                    }
                 }
                )
        """
        if container_name not in self._client.get_batch_containers_metadata():
            raise Exception("This batch container is not allowed to be started")

        metadata = self._client.get_batch_containers_metadata()[container_name]
        if metadata != (None, None, None):
            metadata = (container_name, metadata["description"], metadata["parameters"])
        return metadata

    def get_all_batch_containers_metadata(self):
        """
            Returns the arguments needed for all batch containers.
            :returns:
                a dict of dict in the form
                {
                    "container title": {
                        "description": "container description in restructuredtext",
                        "parameters": {
                            "key":
                            {
                                "type:" "file", #or "text",
                                "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                                "name": "name of the field", #not mandatory in file, default "key"
                                "description": "a short description of what this field is used for", #not mandatory, default ""
                                "custom_key1": "custom_value1",
                                ...
                            }
                        }
                    }
                }
        """
        return self._client.get_batch_containers_metadata()

    def add_batch_job(self, course, container_name, inputdata, launcher_name=None, send_mail=None):
        """
            Add a job in the queue and returns a batch job id.
            inputdata is a dict containing all the keys of get_batch_container_metadata(container_name)["parameters"] BUT the keys "course" and
            "submission" IF their
            type is "file". (the content of the course and the submission will be automatically included by this function.)
            The values associated are file-like objects for "file" types and  strings for "text" types.
        """

        if container_name not in self._client.get_batch_containers_metadata():
            raise Exception("This batch container is not allowed to be started")

        container_args = self._client.get_batch_containers_metadata()[container_name]["parameters"]
        if container_args is None:
            raise Exception("This batch container is not available")

        # Download the course content and submissions and add them to the input
        if "course" in container_args and container_args["course"]["type"] == "file" and "course" not in inputdata:
            inputdata["course"] = self._get_course_data(course)
        if "submissions" in container_args and container_args["submissions"]["type"] == "file" and "submissions" not in inputdata:
            tasks = None
            if "task" in container_args["submissions"] and container_args["submissions"]["task"] in inputdata:
                tasks = [str(inputdata[container_args["submissions"]["task"]])]
            elif "tasks" in container_args["submissions"] and container_args["submissions"]["tasks"] in inputdata:
                tasks = str(inputdata[container_args["submissions"]["tasks"]]).split(",")

            inputdata["submissions"] = self._get_submissions_data(course,
                                                                  tasks,
                                                                  container_args["submissions"].get('folder_format', 'taskid/username'),
                                                                  container_args["submissions"].get('best_only', "0"))

        obj = {"courseid": course.get_id(), 'container_name': container_name, "submitted_on": datetime.now()}

        batch_job_id = self._database.batch_jobs.insert(obj)

        launcher_name = launcher_name or "plugin"

        self._client.new_batch_job(container_name, inputdata,
                                   lambda retval, stdout, stderr, file:
                                   self._batch_job_done_callback(batch_job_id, retval, stdout, stderr, file, send_mail),
                                   launcher_name="Frontend - {}".format(launcher_name))

        return batch_job_id

    def _batch_job_done_callback(self, batch_job_id, retval, stdout, stderr, file, send_mail=None):
        """ Called when the batch job with id jobid has finished.
            :param retval: an integer, the return value of the command in the container
            :param stdout: stdout of the container
            :param stderr: stderr of the container
            :param file: tgz as bytes. Can be None if retval < 0
        """

        result = {
            "retval": retval,
            "stdout": stdout,
            "stderr": stderr,
        }
        if file is not None:
            result["file"] = self._gridfs.put(file)

        # Save submission to database
        self._database.batch_jobs.update(
            {"_id": batch_job_id},
            {"$set": {"result": result}}
        )

        # Send a mail to user
        if send_mail is not None:
            try:
                web.sendmail(web.config.smtp_sendername, send_mail, "Batch job {} finished".format(batch_job_id),
                             """This is an automated message.

The batch job you launched on INGInious is done. You can see the results on the "batch operation" page of your course
administration.""")
            except Exception as e:
                self._logger.error("Cannot send mail: " + str(e))

    def get_batch_job_status(self, batch_job_id):
        """ Returns the batch job with id batch_job_id Batch jobs are dicts in the form
            {"courseid": "...", "container_name": "..."} if the job is still ongoing, and
            {"courseid": "...", "container_name": "...", "results": {}} if the job is done.
            the dict result can be either:

            - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
                if everything went well. (file is an gridfs id to a tgz file)
            - {"retval":"...", "stdout": "...", "stderr":"..."}
                if the container crashed (retval is an int != 0) (can also contain file, but not mandatory)
            - {"retval":-1, "stderr": "the error message"}
                if the container failed to start
        """
        return self._database.batch_jobs.find_one({"_id": ObjectId(batch_job_id)})

    def get_all_batch_jobs_for_course(self, course_id):
        """ Returns all the batch jobs for the course course id. Batch jobs are dicts in the form
            {"courseid": "...", "container_name": "...", "submitted_on":"..."} if the job is still ongoing, and
            {"courseid": "...", "container_name": "...", "submitted_on":"...", "results": {}} if the job is done.
            the dict result can be either:

            - {"retval":0, "stdout": "...", "stderr":"...", "file":"..."}
                if everything went well. (file is an gridfs id to a tgz file)
            - {"retval":"...", "stdout": "...", "stderr":"..."}
                if the container crashed (retval is an int != 0) (can also contain file, but not mandatory)
            - {"retval":-1, "stderr": "the error message"}
                if the container failed to start
        """
        return list(self._database.batch_jobs.find({"courseid": course_id}))

    def drop_batch_job(self, batch_job_id):
        """ Delete a **finished** batch job from the database """
        job = self._database.batch_jobs.find_one({"_id": ObjectId(batch_job_id)})
        if "result" not in job:
            raise Exception("Batch job is still running, cannot delete it")
        self._database.batch_jobs.remove({"_id": ObjectId(batch_job_id)})
        if "file" in job["result"]:
            self._gridfs.delete(job["result"]["file"])
