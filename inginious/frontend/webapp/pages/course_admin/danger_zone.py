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
import glob

from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage


class CourseDangerZonePage(INGIniousAdminPage):
    """ Course administration page: list of classrooms """

    def wipe_course(self, courseid):
        submissions = self.database.submissions.find({"courseid": courseid})
        for submission in submissions:
            for key in ["input", "archive"]:
                if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                    self.submission_manager.get_gridfs().delete(submission[key])

        self.database.classrooms.remove({"courseid": courseid})
        self.database.user_tasks.remove({"courseid": courseid})
        self.database.submissions.remove({"courseid": courseid})

    def dump_course(self, courseid):
        """ Create a zip file containing all information about a given course in database and then remove it from db"""
        filepath = os.path.join(self.backup_dir, courseid, datetime.datetime.now().strftime("%Y%m%d.%H%M%S") + ".zip")

        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        with zipfile.ZipFile(filepath, "w") as zipf:
            classrooms = self.database.classrooms.find({"courseid": courseid}, {"_id": 0})
            zipf.writestr("classrooms.json", bson.json_util.dumps(classrooms), zipfile.ZIP_DEFLATED)

            user_tasks = self.database.user_tasks.find({"courseid": courseid}, {"_id": 0})
            zipf.writestr("user_tasks.json", bson.json_util.dumps(user_tasks), zipfile.ZIP_DEFLATED)

            submissions = self.database.submissions.find({"courseid": courseid}, {"_id": 0})
            zipf.writestr("submissions.json", bson.json_util.dumps(submissions), zipfile.ZIP_DEFLATED)

            submissions.rewind()

            for submission in submissions:
                for key in ["input", "archive"]:
                    if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                        infile = self.submission_manager.get_gridfs().get(submission[key])
                        zipf.writestr(key + "/" + str(submission[key]) + ".data", infile.read(), zipfile.ZIP_DEFLATED)

        self.wipe_course(courseid)

    def restore_course(self, courseid, backup):
        """ Restores a course of given courseid to a date specified in backup (format : YYYYMMDD.HHMMSS) """
        self.wipe_course(courseid)

        filepath = os.path.join(self.backup_dir, courseid, backup + ".zip")
        with zipfile.ZipFile(filepath, "r") as zipf:

            classrooms = bson.json_util.loads(zipf.read("classrooms.json"))
            if len(classrooms) > 0:
                self.database.classrooms.insert(classrooms)

            user_tasks = bson.json_util.loads(zipf.read("user_tasks.json"))
            if len(user_tasks) > 0:
                self.database.user_tasks.insert(user_tasks)

            submissions = bson.json_util.loads(zipf.read("submissions.json"))
            for submission in submissions:
                for key in ["input", "archive"]:
                    if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                        submission[key] = self.submission_manager.get_gridfs().put(zipf.read(key + "/" + str(submission[key]) + ".data"))

            self.database.submissions.insert(submissions)

    def GET(self, courseid):
        """ GET request """
        if not self.user_manager.user_is_superadmin(self.user_manager.session_username()):
            raise web.notfound()

        data = web.input()

        if "download" in data:
            filepath = os.path.join(self.backup_dir, courseid, data["download"] + '.zip')

            if not os.path.exists(os.path.dirname(filepath)):
                raise web.notfound()

            web.header('Content-Type', 'application/zip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="lol.zip"', unique=True)

            return open(filepath, 'rb')

        else:
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
                    msg = "An error occured while dumping course from database."
                    error = True
        elif "restore" in data:
            if not data["token"] == self.user_manager.session_token():
                msg = "Operation aborted due to invalid token."
                error = True
            elif "backupdate" not in data:
                msg = "No backup date selected."
                error = True
            else:
                try:
                    dt = datetime.datetime.strptime(data["backupdate"], "%Y%m%d.%H%M%S")
                    self.restore_course(courseid, data["backupdate"])
                    msg = "Course restored to date : " + dt.strftime("%Y-%m-%d %H:%M:%S") + "."
                except:
                    raise
                    msg = "An error occured while restoring backup."
                    error = True

        course = self.course_factory.get_course(courseid)
        return self.page(course, msg, error)

    def page(self, course, msg="", error=False):
        """ Get all data and display the page """
        thehash = hashlib.sha512(str(random.getrandbits(256))).hexdigest()
        self.user_manager.set_session_token(thehash)

        backups = []

        filepath = os.path.join(self.backup_dir, course.get_id())
        if os.path.exists(os.path.dirname(filepath)):
            for backup in glob.glob(os.path.join(filepath, '*.zip')):
                try:
                    basename = os.path.basename(backup)[0:-4]
                    dt = datetime.datetime.strptime(basename, "%Y%m%d.%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                    backups.append({"file": basename, "date": dt})
                except: # Wrong format
                    pass

        return self.template_helper.get_renderer().course_admin.danger_zone(course, thehash, backups, msg, error)
