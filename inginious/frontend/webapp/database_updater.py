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
""" Updates the database """
import pymongo


def update_database(database, gridfs, course_factory, user_manager):
    """
    Checks the database version and update the db if necessary
    :param course_factory: the course factory
    """

    db_version = database.db_version.find_one({})
    if db_version is None:
        db_version = 0
    else:
        db_version = db_version['db_version']

    if db_version < 1:
        print "Updating database to db_version 1"
        # Init the database
        database.submissions.ensure_index([("username", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        database.submissions.ensure_index([("submitted_on", pymongo.DESCENDING)])  # sort speed

        database.user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)],
                                         unique=True)
        database.user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING)])
        database.user_tasks.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
        database.user_tasks.ensure_index([("courseid", pymongo.ASCENDING)])
        database.user_tasks.ensure_index([("username", pymongo.ASCENDING)])

        db_version = 1

    if db_version < 2:
        print "Updating database to db_version 2"
        # Register users that submitted some tasks to the related courses
        data = database.user_tasks.aggregate([{"$group": {"_id": "$courseid", "usernames": {"$addToSet": "$username"}}}])
        for r in list(data):
            try:
                course = course_factory.get_course(r['_id'])
                for u in r['usernames']:
                    user_manager.course_register_user(course, u, force=True)
            except:
                print "There was an error while updating the database. Some users may have been unregistered from the course {}".format(r['_id'])
        db_version = 2

    if db_version < 3:
        print "Updating database to db_version 3"
        # Add the grade for all the old submissions
        database.submissions.update({}, {"$set": {"grade": 0.0}}, multi=True)
        database.submissions.update({"result": "success"}, {"$set": {"grade": 100.0}}, multi=True)
        database.user_tasks.update({}, {"$set": {"grade": 0.0}}, multi=True)
        database.user_tasks.update({"succeeded": True}, {"$set": {"grade": 100.0}}, multi=True)
        db_version = 3

    if db_version < 4:
        print "Updating database to db_version 4"
        submissions = database.submissions.find({"$where": "!Array.isArray(this.username)"})
        for submission in submissions:
            submission["username"] = [submission["username"]]
            database.submissions.save(submission)
        db_version = 4

    if db_version < 5:
        print "Updating database to db_version 5"
        database.drop_collection("users")
        database.submissions.update_many({}, {"$set": {"response_type": "html"}})
        db_version = 5

    if db_version < 6:
        print "Updating database to db_version 6"
        course_list = list(database.registration.aggregate([
            {"$match": {}},
            {
                "$group": {
                    "_id": "$courseid",
                    "students": {"$addToSet": "$username"}
                }
            }]))

        classrooms = {}
        for course in course_list:
            classrooms[course["_id"]] = {"courseid": course["_id"], "groups": [], "description": "Default classroom", "default": True, "students": course["students"], "tutors": set([])}

        group_list = list(database.groups.find({}, {'_id': 0}))
        for group in group_list:
            classrooms[group["course_id"]]["groups"].append({"size": group["size"], "students": group["users"]})
            classrooms[group["course_id"]]["tutors"] = classrooms[group["course_id"]]["tutors"].union(group["tutors"])

        for i, classroom in classrooms.iteritems():
            classroom["tutors"] = list(classroom["tutors"])
            database.classrooms.insert(classroom)

        database.classrooms.create_index([("students", pymongo.ASCENDING)])
        database.classrooms.create_index([("groups.students", pymongo.ASCENDING)])

        db_version = 6

    database.db_version.update({}, {"$set": {"db_version": db_version}}, upsert=True)
