# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Main page for the LTI provider. Displays a task and allow to answer to it. """
from threading import Thread

import web
import os
import shutil

from inginious.frontend.lti.pages.utils import LTIAuthenticatedPage

download_status = []


class LTIDownload(LTIAuthenticatedPage):
    def required_role(self, method="POST"):
        return self.admin_role

    def LTI_GET(self, users_arg, tasks_arg):
        all_users = users_arg == "all"
        all_tasks = tasks_arg == "all"

        search_dict = {"courseid": self.course.get_id(), "status": {"$in": ["done", "error"]}}
        if not all_tasks:
            search_dict["taskid"] = self.task.get_id()
        if not all_users:
            search_dict["username"] = self.user_manager.session_username()

        dl_tag = len(download_status)
        download_status.append("starting")

        thread = ArchiverThread(dl_tag, self.database.submissions.find(search_dict), self.submission_manager.get_submission_archive, self.app.download_directory)
        thread.start()

        return "Progress can be displayed at download/"+str(dl_tag)


class ArchiverThread(Thread):
    def __init__(self, dl_tag, submissions, get_submission_archive, download_directory):
        super(ArchiverThread, self).__init__()
        self.dl_tag = dl_tag
        self.submission = list(submissions)  # copy
        self.get_submission_archive = get_submission_archive
        self.download_directory = download_directory

    def run(self):
        download_status[self.dl_tag] = "listing submissions"
        self.get_submission_archive(self.iterate_and_update(), ['taskid', 'username'], [],
                                    open(os.path.join(self.download_directory, str(self.dl_tag) + ".tgz"), "wb"))
        download_status[self.dl_tag] = "done"

    def iterate_and_update(self):
        idx = 0
        total = len(self.submission)
        while len(self.submission) != 0:
            s = self.submission.pop()
            idx += 1
            download_status[self.dl_tag] = "archiving "+str(idx)+"/"+str(total)
            yield s


class LTIDownloadStatus(LTIAuthenticatedPage):
    def required_role(self, method="POST"):
        return self.admin_role

    def LTI_GET(self, dl_tag):
        dl_tag = int(dl_tag)
        if dl_tag < 0 or dl_tag >= len(download_status):
            return "This archive does not exists"

        if download_status[dl_tag] == "done":
            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
            return open(os.path.join(self.app.download_directory, str(dl_tag)+".tgz"), 'rb').read()
        else:
            return str(download_status[dl_tag])
