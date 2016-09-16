# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages submissions """
import pymongo

from inginious.frontend.common.submission_manager import SubmissionManager


class WebAppSubmissionManager(SubmissionManager):
    """ Manages submissions. Communicates with the database and the client. """

    def __init__(self, client, user_manager, database, gridfs, hook_manager):
        """
        :type client: inginious.client.client.AbstractClient
        :type user_manager: inginious.frontend.common.user_manager.AbstractUserManager
        :type database: pymongo.database.Database
        :type gridfs: gridfs.GridFS
        :type hook_manager: inginious.common.hook_manager.HookManager
        :return:
        """
        super(WebAppSubmissionManager, self).__init__(client, user_manager, database, gridfs, hook_manager)

    def _job_done_callback(self, submissionid, task, result, grade, problems, tests, custom, archive):
        """ Callback called by Client when a job is done. Updates the submission in the database with the data returned after the completion of the
        job """
        super(WebAppSubmissionManager, self)._job_done_callback(submissionid, task, result, grade, problems, tests, custom, archive)

        submission = self.get_submission(submissionid, False)
        for username in submission["username"]:
            self._user_manager.update_user_stats(username, task, submission, result[0], grade)

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

    def _always_keep_best(self):
        return False
