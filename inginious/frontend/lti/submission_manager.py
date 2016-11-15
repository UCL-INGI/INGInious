# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A custom Submission Manager that removes exceeding submissions """
import threading
import logging

from inginious.frontend.common.submission_manager import SubmissionManager


class LTISubmissionManager(SubmissionManager):
    """ A custom Submission Manager that removes exceeding submissions """

    def __init__(self, client, user_manager, database, gridfs, hook_manager, max_submissions, lis_outcome_manager):
        self._max_submissions = max_submissions
        super(LTISubmissionManager, self).__init__(client, user_manager, database, gridfs, hook_manager)
        self.lis_outcome_data = {}
        self.lis_outcome_data_lock = threading.Lock()
        self.lis_outcome_manager = lis_outcome_manager
        self._logger = logging.getLogger("inginious.lti.submissions")

    def _after_submission_insertion(self, task, inputdata, debug, submission, submissionid):
        self.lis_outcome_data_lock.acquire()
        self.lis_outcome_data[submissionid] = (self._user_manager.session_consumer_key(),
                                               self._user_manager.session_outcome_service_url(),
                                               self._user_manager.session_outcome_result_id())
        self.lis_outcome_data_lock.release()
        return self._delete_exceeding_submissions(self._user_manager.session_username(), task, self._max_submissions)

    def _job_done_callback(self, submissionid, task, result, grade, problems, tests, custom, archive, stdout, stderr, newsub=False):
        super(LTISubmissionManager, self)._job_done_callback(submissionid, task, result, grade, problems, tests, custom, archive, stdout, stderr, newsub)

        # Send data to the TC
        self.lis_outcome_data_lock.acquire()
        data = self.lis_outcome_data[submissionid]
        del self.lis_outcome_data[submissionid]
        self.lis_outcome_data_lock.release()

        submission = self.get_submission(submissionid, False)
        self.lis_outcome_manager.add(submission["username"], submission["courseid"], submission["taskid"], data[0], data[1], data[2])

    def _always_keep_best(self):
        return True
