# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A custom Submission Manager that removes exceeding submissions """
import threading

import pymongo

from inginious.frontend.common.submission_manager import SubmissionManager

import logging


class LTISubmissionManager(SubmissionManager):
    """ A custom Submission Manager that removes exceeding submissions """

    def __init__(self, job_manager, user_manager, database, gridfs, hook_manager, max_submissions, lis_outcome_manager):
        self._max_submissions = max_submissions
        super(LTISubmissionManager, self).__init__(job_manager, user_manager, database, gridfs, hook_manager)
        self.lis_outcome_data = {}
        self.lis_outcome_data_lock = threading.Lock()
        self.lis_outcome_manager = lis_outcome_manager
        self._logger = logging.getLogger("inginious.lti.submission_manager")

    def add_job(self, task, inputdata, debug=False):
        debug = bool(debug)  # do not allow "ssh" here
        return super(LTISubmissionManager, self).add_job(task, inputdata, debug)

    def _after_submission_insertion(self, task, inputdata, debug, submission, submissionid):
        self.lis_outcome_data_lock.acquire()
        self.lis_outcome_data[submissionid] = (self._user_manager.session_consumer_key(),
                                               self._user_manager.session_outcome_service_url(),
                                               self._user_manager.session_outcome_result_id(),
                                               self._user_manager.session_realname(),
                                               self._user_manager.session_email(),
        )
        self.lis_outcome_data_lock.release()

        return self._delete_exceeding_submissions(self._user_manager.session_username(), task, self._max_submissions)

    def _job_done_callback(self, submissionid, task, job):
        super(LTISubmissionManager, self)._job_done_callback(submissionid, task, job)

        # Send data to the TC

        self.lis_outcome_data_lock.acquire()
        data = self.lis_outcome_data[submissionid]
        del self.lis_outcome_data[submissionid]
        self.lis_outcome_data_lock.release()

        consumer_key, outcome_service_url, outcome_result_id, realname, email = data

        submission = self.get_submission(submissionid, False)
        
        courseid = submission["courseid"]
        taskid = submission["taskid"]
        username = submission["username"]

        if isinstance(username, list):
            # I do not know why the username is a list...dcg
            username = username[0]
        result, grade = self._user_manager.get_task_result_grade(task, username)

        self.lis_outcome_manager.add(username, courseid, taskid,
                                     consumer_key, outcome_service_url, outcome_result_id,
                                     result, grade, realname, email, submission)

    def _always_keep_best(self):
        return True
