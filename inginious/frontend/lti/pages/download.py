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
""" Main page for the LTI provider. Displays a task and allow to answer to it. """
from threading import Thread

import web
import os
import shutil

from inginious.frontend.lti.pages.utils import LTIAuthenticatedPage

if os.path.exists(os.path.join("lti_download", "tmp")):
    shutil.rmtree(os.path.join("lti_download", "tmp"))
os.mkdir(os.path.join("lti_download", "tmp"))

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

        thread = ArchiverThread(dl_tag, self.database.submissions.find(search_dict), self.submission_manager.get_submission_archive)
        thread.start()

        return "Progress can be displayed at download/"+str(dl_tag)


class ArchiverThread(Thread):
    def __init__(self, dl_tag, submission_cursor, get_submission_archive):
        self.dl_tag = dl_tag
        self.submission_cursor = submission_cursor
        self.get_submission_archive = get_submission_archive
        super(ArchiverThread, self).__init__()

    def run(self):
        download_status[self.dl_tag] = "listing submissions"
        self.get_submission_archive(self.iterate_and_update(), ['taskid', 'username'], [],
                                    open(os.path.join("lti_download", "tmp", str(self.dl_tag) + ".tgz")))
        download_status[self.dl_tag] = "done"

    def iterate_and_update(self):
        idx = 0
        total = self.submission_cursor.count()
        for s in self.submission_cursor:
            download_status[self.dl_tag] = "archiving "+str(idx)+"/"+str(total)
            yield s


class LTIDownloadStatus(LTIAuthenticatedPage):
    def required_role(self, method="POST"):
        return self.admin_role

    def LTI_GET(self, dl_tag):
        dl_tag = int(dl_tag)
        if dl_tag not in download_status:
            return "This archive does not exists"

        if download_status[dl_tag] == "done":
            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="submissions.tgz"', unique=True)
            return open(os.path.join("lti_download", "tmp", str(dl_tag)+".tgz"))
        else:
            return str(download_status[dl_tag])