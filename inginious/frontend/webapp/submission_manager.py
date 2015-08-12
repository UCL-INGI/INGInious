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
from datetime import datetime
import json
from inginious.frontend.common.submission_manager import SubmissionManager


class WebAppSubmissionManager(SubmissionManager):
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
        super(WebAppSubmissionManager, self).__init__(job_manager, user_manager, database, gridfs, hook_manager)

    def _job_done_callback(self, submissionid, task, job):
        """ Callback called by JobManager when a job is done. Updates the submission in the database with the data returned after the completion of the job """
        super(WebAppSubmissionManager, self)._job_done_callback(submissionid, task, job)

        submission = self.get_submission(submissionid, False)
        for username in submission["username"]:
            self._user_manager.update_user_stats(username, submission, job)

    def add_job(self, task, inputdata, debug=False):
        """ Add a job in the queue and returns a submission id.
            task is a Task instance and inputdata is the input as a dictionary
            If debug is true, more debug data will be saved.
            If debug is set to "ssh", a remote ssh server will be started
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
            "response_type": task.get_response_type()
        }

        if task.is_group_task() and not self._user_manager.has_staff_rights_on_course(task.get_course(), username):
            group = self._database.classrooms.find_one(
                {"courseid": task.get_course_id(), "groups.students": username},
                {"groups": {"$elemMatch": {"students": username}}})

            obj.update({"username": group["groups"][0]["students"]})
        else:
            obj.update({"username": [username]})

        submissionid = self._database.submissions.insert(obj)

        self._hook_manager.call_hook("new_submission", submissionid=submissionid, submission=obj, inputdata=inputdata)

        ssh_callback = None
        if debug == "ssh":
            ssh_callback = lambda conn_id, ssh_key: self._handle_ssh_callback(submissionid, conn_id, ssh_key)

        self._job_manager.new_job(task, inputdata, (lambda job: self._job_done_callback(submissionid, task, job)), "Frontend - {}".format(username),
                                  debug, ssh_callback)

        return submissionid

    def _handle_ssh_callback(self, submission_id, conn_id, ssh_key):
        """ Handles the creation of a remote ssh server """
        if ssh_key != "": #ignore late calls (a bit hacky, but...)
            obj = {
                "ssh_internal_conn_id": conn_id,
                "ssh_key": ssh_key
            }
            self._database.submissions.update_one({"_id": submission_id}, {"$set": obj})