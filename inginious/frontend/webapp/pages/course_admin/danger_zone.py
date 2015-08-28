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


import hashlib
import random
import web
import bson.json_util
import os
import datetime
import zipfile
import tempfile
from gridfs import GridFS

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseDangerZonePage(INGIniousAdminPage):
    """ Course administration page: list of classrooms """

    def dump_course(self, courseid):
        filepath = os.path.join(self.backup_dir, courseid + datetime.datetime.now().strftime("%Y%m%d.%H%M%S") + ".zip")

        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        with zipfile.ZipFile(filepath, "w") as zipf:
            classrooms = self.database.classrooms.find({"courseid": courseid})
            zipf.writestr("classrooms.json", bson.json_util.dumps(classrooms), zipfile.ZIP_DEFLATED)

            user_tasks = self.database.user_tasks.find({"courseid": courseid})
            zipf.writestr("user_tasks.json", bson.json_util.dumps(user_tasks), zipfile.ZIP_DEFLATED)

            submissions = self.database.submissions.find({"courseid": courseid})
            zipf.writestr("submissions.json", bson.json_util.dumps(submissions), zipfile.ZIP_DEFLATED)

            submissions.rewind()

            for submission in submissions:
                for key in ["input", "archive"]:
                    if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                        infile = self.submission_manager.get_gridfs().get(submission[key])
                        zipf.writestr(os.path.join(key, str(submission[key]) + ".data"), infile.read(), zipfile.ZIP_DEFLATED)

        self.database.classrooms.remove({"courseid": courseid})
        self.database.user_tasks.remove({"courseid": courseid})
        self.database.submissions.remove({"courseid": courseid})

    def GET(self, courseid):
        """ GET request """
        if not self.user_manager.user_is_superadmin(self.user_manager.session_username()):
            raise web.notfound()

        course = self.course_factory.get_course(courseid)
        return self.page(course)

    def POST(self, courseid):
        """ POST request """
        if not self.user_manager.user_is_superadmin(self.user_manager.session_username()):
            raise web.notfound()

        msg = ""
        error = False

        data = web.input()
        if "wipeall" in data:
            if not data["token"] == self.user_manager.session_token():
                msg = "Operation aborted due to invalid token."
                error = True
            elif not data["courseid"] == courseid:
                msg = "Wrong course id."
                error = True
            else:
                try:
                    self.dump_course(courseid)
                    msg = "All course data have been deleted."
                except:
                    raise
                    msg = "An error occured while dumping course from database."
                    error = True

        course = self.course_factory.get_course(courseid)
        return self.page(course, msg, error)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        thehash = hashlib.sha512(str(random.getrandbits(256))).hexdigest()
        self.user_manager.set_session_token(thehash)

        return self.template_helper.get_renderer().course_admin.danger_zone(course, thehash, msg, error)
