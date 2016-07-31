# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A custom Submission Manager that removes exceeding submissions """
import threading

import pymongo

from inginious.frontend.common.submission_manager import SubmissionManager


class LTISubmissionManager(SubmissionManager):
    """ A custom Submission Manager that removes exceeding submissions """

    def __init__(self, client, user_manager, database, gridfs, hook_manager, max_submissions, lis_outcome_manager):
        self._max_submissions = max_submissions
        super(LTISubmissionManager, self).__init__(client, user_manager, database, gridfs, hook_manager)
        self.lis_outcome_data = {}
        self.lis_outcome_data_lock = threading.Lock()
        self.lis_outcome_manager = lis_outcome_manager

    def add_job(self, task, inputdata, debug=False):
        debug = bool(debug)  # do not allow "ssh" here
        return super(LTISubmissionManager, self).add_job(task, inputdata, debug)

    def _after_submission_insertion(self, task, inputdata, debug, submission, submissionid):
        self.lis_outcome_data_lock.acquire()
        self.lis_outcome_data[submissionid] = (self._user_manager.session_consumer_key(),
                                               self._user_manager.session_outcome_service_url(),
                                               self._user_manager.session_outcome_result_id())
        self.lis_outcome_data_lock.release()
        self._delete_exceeding_submissions(self._user_manager.session_username(), task.get_course_id(), task.get_id())

    def _job_done_callback(self, submissionid, task, result, grade, problems, tests, custom, archive):
        super(LTISubmissionManager, self)._job_done_callback(submissionid, task, result, grade, problems, tests, custom, archive)

        # Send data to the TC
        self.lis_outcome_data_lock.acquire()
        data = self.lis_outcome_data[submissionid]
        del self.lis_outcome_data[submissionid]
        self.lis_outcome_data_lock.release()

        submission = self.get_submission(submissionid, False)
        self.lis_outcome_manager.add(submission["username"], submission["courseid"], submission["taskid"], data[0], data[1], data[2])

    def _delete_exceeding_submissions(self, username, course_id, task_id):
        """ Deletes exceeding submissions from the database, to keep the database relatively small """

        if self._max_submissions <= 0:
            return
        tasks = list(self._database.submissions.find({"username": username, "courseid": course_id, "taskid": task_id},
                                                     projection=["_id", "status", "result", "grade"],
                                                     sort=[('submitted_on', pymongo.DESCENDING)]))

        # Find the best "status"="done" and "result"="success"
        idx_best = -1
        for idx, val in enumerate(tasks):
            if val["status"] == "done" and val["result"] == "success":
                if idx_best == -1 or tasks[idx_best]["grade"] < val["grade"]:
                    idx_best = idx

        # List the entries to keep
        to_keep = set()

        # Always keep the best submission
        if idx_best != -1:
            to_keep.add(tasks[idx_best]["_id"])

        # Always keep running submissions
        for val in tasks:
            if val["status"] == "waiting":
                to_keep.add(val["_id"])

        while len(to_keep) < self._max_submissions and len(tasks) > 0:
            to_keep.add(tasks.pop()["_id"])

        to_delete = {val["_id"] for val in tasks}.difference(to_keep)
        self._database.submissions.delete_many({"_id": {"$in": list(to_delete)}})
