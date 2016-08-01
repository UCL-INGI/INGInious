# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages submissions """
import pymongo

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
            self._user_manager.update_user_stats(username, task, submission, job)

    def _before_submission_insertion(self, task, inputdata, debug, obj):
        username = self._user_manager.session_username()

        if task.is_group_task() and not self._user_manager.has_staff_rights_on_course(task.get_course(), username):
            group = self._database.aggregations.find_one(
                {"courseid": task.get_course_id(), "groups.students": username},
                {"groups": {"$elemMatch": {"students": username}}})

            obj.update({"username": group["groups"][0]["students"]})
        else:
            obj.update({"username": [username]})

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

    def _delete_exceeding_submissions(self, username, task, max_submissions_bound=-1):
        """ Deletes exceeding submissions from the database, to keep the database relatively small """

        if max_submissions_bound <= 0:
            max_submissions = task.get_stored_submissions()
        elif task.get_stored_submissions() <= 0:
            max_submissions = max_submissions_bound
        else:
            max_submissions = min(max_submissions_bound, task.get_stored_submissions())

        if max_submissions <= 0:
            return
        tasks = list(self._database.submissions.find(
            {"username": username, "courseid": task.get_course_id(), "taskid": task.get_id()},
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

        while len(to_keep) < max_submissions and len(tasks) > 0:
            to_keep.add(tasks.pop()["_id"])

        to_delete = {val["_id"] for val in tasks}.difference(to_keep)
        self._database.submissions.delete_many({"_id": {"$in": list(to_delete)}})
        return to_delete[0]