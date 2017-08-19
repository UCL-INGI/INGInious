# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages submissions """
import bson
import logging
from datetime import datetime

from inginious.frontend.common.submission_manager import SubmissionManager


class WebAppSubmissionManager(SubmissionManager):
    """ Manages submissions. Communicates with the database and the client. """

    def __init__(self, client, user_manager, database, gridfs, hook_manager, lti_outcome_manager):
        """
        :type client: inginious.client.client.AbstractClient
        :type user_manager: inginious.frontend.common.user_manager.AbstractUserManager
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type hook_manager: inginious.common.hook_manager.HookManager
        :return:
        """
        super(WebAppSubmissionManager, self).__init__(client, user_manager, database, gridfs, hook_manager)
        self._logger = logging.getLogger("inginious.webapp.submissions")
        self._lti_outcome_manager = lti_outcome_manager

    def _job_done_callback(self, submissionid, task, result, grade, problems, tests, custom, archive, stdout, stderr, newsub=True):
        """ Callback called by Client when a job is done. Updates the submission in the database with the data returned after the completion of the
        job """
        super(WebAppSubmissionManager, self)._job_done_callback(submissionid, task, result, grade, problems, tests, custom, archive, stdout, stderr, newsub)

        submission = self.get_submission(submissionid, False)
        for username in submission["username"]:
            self._user_manager.update_user_stats(username, task, submission, result[0], grade, newsub)

        if "outcome_service_url" in submission and "outcome_result_id" in submission and "outcome_consumer_key" in submission:
            for username in submission["username"]:
                self._lti_outcome_manager.add(username,
                                              submission["courseid"],
                                              submission["taskid"],
                                              submission["outcome_consumer_key"],
                                              submission["outcome_service_url"],
                                              submission["outcome_result_id"])

    def _before_submission_insertion(self, task, inputdata, debug, obj):
        username = self._user_manager.session_username()

        if task.is_group_task() and not self._user_manager.has_staff_rights_on_course(task.get_course(), username):
            group = self._database.aggregations.find_one(
                {"courseid": task.get_course_id(), "groups.students": username},
                {"groups": {"$elemMatch": {"students": username}}})

            obj.update({"username": group["groups"][0]["students"]})
        else:
            obj.update({"username": [username]})

        lti_info = self._user_manager.session_lti_info()
        if lti_info is not None and task.get_course().lti_send_back_grade():
            outcome_service_url = lti_info["outcome_service_url"]
            outcome_result_id = lti_info["outcome_result_id"]
            outcome_consumer_key = lti_info["consumer_key"]

            # safety check
            if outcome_result_id is None or outcome_service_url is None:
                self._logger.error("outcome_result_id or outcome_service_url is None, but grade needs to be sent back to TC! Ignoring.")
                return

            obj.update({"outcome_service_url": outcome_service_url,
                        "outcome_result_id": outcome_result_id,
                        "outcome_consumer_key": outcome_consumer_key})

    def _after_submission_insertion(self, task, inputdata, debug, submission, submissionid):
        # If we are submitting for a group, send the group (user list joined with ",") as username
        if "group" not in [p.get_id() for p in task.get_problems()]:  # do not overwrite
            username = self._user_manager.session_username()
            if task.is_group_task() and not self._user_manager.has_staff_rights_on_course(task.get_course(), username):
                group = self._database.aggregations.find_one(
                    {"courseid": task.get_course_id(), "groups.students": username},
                    {"groups": {"$elemMatch": {"students": username}}})
                inputdata["username"] = ','.join(group["groups"][0]["students"])

        return self._delete_exceeding_submissions(self._user_manager.session_username(), task)

    def _always_keep_best(self):
        return False

    def replay_job(self, task, submission, copy=False, debug=False):
        """
        Replay a submission: add the same job in the queue, keeping submission id, submission date and input data
        :param submission: Submission to replay
        :param copy: If copy is true, the submission will be copied to admin submissions before replay
        :param debug: If debug is true, more debug data will be saved
        """
        if not self._user_manager.session_logged_in():
            raise Exception("A user must be logged in to submit an object")

        # Don't enable ssh debug
        ssh_callback = lambda host, port, password: None
        if debug == "ssh":
            ssh_callback = lambda host, port, password: self._handle_ssh_callback(submission["_id"], host, port, password)

        # Load input data and add username to dict
        inputdata = bson.BSON.decode(self._gridfs.get(submission["input"]).read())

        if not copy:
            submissionid = submission["_id"]
            username = submission["username"][0] # TODO: this may be inconsistent with add_job

            # Remove the submission archive : it will be regenerated
            if submission.get("archive", None) is not None:
                self._gridfs.delete(submission["archive"])
        else:
            del submission["_id"]
            username = self._user_manager.session_username()
            submission["username"] = [username]
            submission["submitted_on"] = datetime.now()
            submissionid = self._database.submissions.insert(submission)

        if "username" not in [p.get_id() for p in task.get_problems()]:  # do not overwrite
            inputdata["username"] = username

        jobid = self._client.new_job(task, inputdata,
                                     (lambda result, grade, problems, tests, custom, archive, stdout, stderr:
                                      self._job_done_callback(submissionid, task, result, grade, problems, tests, custom, archive, stdout, stderr, copy)),
                                     "Frontend - {}".format(submission["username"]), debug, ssh_callback)

        # Clean the submission document in db
        self._database.submissions.update(
            {"_id": submission["_id"]},
            {"$set": {"jobid": jobid, "status": "waiting", "response_type": task.get_response_type()},
             "$unset": {"result": "", "grade": "", "text": "", "tests": "", "problems": "", "archive": "", "custom": ""}
             })

        if not copy:
            self._logger.info("Replaying submission %s - %s - %s - %s", submission["username"], submission["courseid"],
                              submission["taskid"], submission["_id"])
        else:
            self._logger.info("Copying submission %s - %s - %s - %s as %s", submission["username"], submission["courseid"],
                              submission["taskid"], submission["_id"], self._user_manager.session_username())
