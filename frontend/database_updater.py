# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
""" Updates the database """
import pymongo
from frontend.base import get_database
from frontend.custom.courses import FrontendCourse


def update_database():
    db_version = get_database().db_version.find_one({})
    if db_version is None:
        db_version = 0
    else:
        db_version = db_version['db_version']

    if db_version < 1:
        print "Updating database to db_version 1"
        # Init the database
        get_database().submissions.ensure_index([("username", pymongo.ASCENDING)])
        get_database().submissions.ensure_index([("courseid", pymongo.ASCENDING)])
        get_database().submissions.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        get_database().submissions.ensure_index([("submitted_on", pymongo.DESCENDING)])  # sort speed

        get_database().user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)], unique=True)
        get_database().user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING)])
        get_database().user_tasks.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        get_database().user_tasks.ensure_index([("courseid", pymongo.ASCENDING)])
        get_database().user_tasks.ensure_index([("username", pymongo.ASCENDING)])

        db_version = 1

    if db_version < 2:
        print "Updating database to db_version 2"
        # Register users that submitted some tasks to the related courses
        data = get_database().user_tasks.aggregate([{"$group": {"_id": "$courseid", "usernames": {"$addToSet": "$username"}}}])
        for r in data['result']:
            try:
                course = FrontendCourse(r['_id'])
                for u in r['usernames']:
                    course.register_user(u, force=True)
            except:
                print "There was an error while updating the database. Some users may have been unregistered from the course {}".format(r['_id'])
        db_version = 2

    get_database().db_version.update({}, {"$set": {"db_version": db_version}}, upsert=True)
