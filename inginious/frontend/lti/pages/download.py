# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Main page for the LTI provider. Displays a task and allow to answer to it. """
from threading import Thread
import pymongo
import web
import hashlib
import random
import os
import json
from collections import OrderedDict

from inginious.common.base import id_checker
from inginious.frontend.lti.pages.utils import LTIAuthenticatedPage


class LTIDownload(LTIAuthenticatedPage):
    """
    Download page for LTI submissions
    """

    def required_role(self, method="POST"):
        return self.admin_role

    def _validate_list(self, usernames):
        """ Prevent MongoDB injections by verifying arrays sent to it """
        for i in usernames:
            if not id_checker(i):
                raise web.notfound()

    def valid_formats(self):
        """ Returns the supported download formats"""
        return ["taskid/username", "username/taskid"]

    def get_selected_submissions(self, course, selected_tasks, users, stype):
        """
        Returns the submissions that have been selected by the admin
        :param course: course
        :param selected_tasks: selected tasks id
        :param users: selected usernames
        :param stype: single or all submissions
        :return:
        """
        self._validate_list(users)
        submissionsid = []
        if stype == "single":
            tasks = self.course.get_tasks()
            for taskid in selected_tasks:
                task = tasks[taskid]
                if task.get_evaluate() == "last":
                    submissionsid.extend([result["submissionid"] for result in self.database.submissions.aggregate([
                        {"$unwind": "$username"},
                        {"$match": {"username": {"$in": users}, "taskid": task.get_id(),
                                    "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}},
                        {"$sort": {"submitted_on": pymongo.DESCENDING}},
                        {"$group": {"_id": "$username", "submissionid": {"$first": "$_id"},
                                    "submitted_on": {"$first": "$submitted_on"}}}
                    ])])
                else:  #best
                    submissionsid.extend([result["submissionid"] for result in self.database.submissions.aggregate([
                        {"$unwind": "$username"},
                        {"$match": {"username": {"$in": users}, "taskid": task.get_id(),
                                    "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}},
                        {"$sort": {"grade": pymongo.DESCENDING}},
                        {"$group": {"_id": "$username", "submissionid": {"$first": "$_id"},
                                    "grade": {"$first": "$grade"}}}
                    ])])

            submissions = list(self.database.submissions.find({"_id": {"$in": submissionsid}}))
        else:
            submissions = list(self.database.submissions.find({"username": {"$in": users},
                                                               "taskid": {"$in": selected_tasks},
                                                               "courseid": course.get_id(),
                                                               "status": {"$in": ["done", "error"]}}))
        return submissions

    def LTI_POST(self):
        user_input = web.input(tasks=[], users=[])

        if "status" in user_input:
            dl_tag = user_input.get("tag", "")
            if dl_tag not in self.app.download_status:
                return json.dumps({"status": "error", "msg": "This archive does not exist."})
            else:
                return json.dumps({"status": "done", "result": self.app.download_status[dl_tag]})

        if "type" not in user_input or "format" not in user_input or user_input.format not in self.valid_formats():
            raise web.notfound()

        tasks = list(self.course.get_tasks().keys())
        for i in user_input.tasks:
            if i not in tasks:
                raise web.notfound()

        # Load submissions
        submissions = self.get_selected_submissions(self.course, user_input.tasks, user_input.users, user_input.type)

        dl_tag = hashlib.md5(str(random.getrandbits(256)).encode("utf-8")).hexdigest() + ".tgz"

        self.app.download_status[dl_tag] = False

        thread = ArchiverThread(self.app.download_status, dl_tag, submissions, self.submission_manager.get_submission_archive,
                                os.path.join(self.app.download_directory, dl_tag), list(reversed(user_input.format.split('/'))))
        thread.start()

        return json.dumps({"status": "done", "tag":  dl_tag, "session": self.user_manager.get_session_identifier()})

    def LTI_GET(self):
        user_input = web.input()

        if "archive" in user_input:
            dl_tag = user_input.archive
            if not self.app.download_status.get(dl_tag, False):
                raise web.notfound()

            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
            return open(os.path.join(self.app.download_directory, dl_tag), 'rb').read()

        tasks = sorted(list(self.course.get_tasks().items()), key=lambda task: (task[1].get_order(), task[1].get_id()))

        user_list = self.database.submissions.aggregate([{"$unwind": "$username"}, {"$group": {"_id": "$username"}}])
        user_data = OrderedDict(
            [(user['_id'], user['_id']) for user in user_list])

        return self.template_helper.get_renderer().download(self.course, self.task.get_id(), tasks, user_data, self.valid_formats())


class ArchiverThread(Thread):
    """
    Thread exporting a list of selected submissions into an archive file
    """

    def __init__(self, dl_status, dl_tag, submissions, get_submission_archive, filename, sformat):
        super(ArchiverThread, self).__init__()
        self.dl_status = dl_status
        self.dl_tag = dl_tag
        self.submissions = list(submissions)  # copy
        self.get_submission_archive = get_submission_archive
        self.filename = filename
        self.sformat = sformat

    def run(self):
        self.dl_status[self.dl_tag] = False
        self.get_submission_archive(self.submissions, self.sformat, [], open(self.filename, "wb"))
        self.dl_status[self.dl_tag] = True
