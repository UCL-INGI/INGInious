# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Updates the database """
import json

import bson
import pymongo
import logging


def update_database(database, gridfs, course_factory, user_manager):  # pylint: disable=unused-argument
    """
    Checks the database version and update the db if necessary
    :param course_factory: the course factory
    """

    logger = logging.getLogger("inginious.db_update")

    db_version = database.db_version.find_one({})
    if db_version is None:
        db_version = 0
    else:
        db_version = db_version['db_version']

    if db_version < 1:
        logger.info("Updating database to db_version 1")
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
        logger.info("Updating database to db_version 2")
        # Register users that submitted some tasks to the related courses
        data = database.user_tasks.aggregate([{"$group": {"_id": "$courseid", "usernames": {"$addToSet": "$username"}}}])
        for r in list(data):
            try:
                course = course_factory.get_course(r['_id'])
                for u in r['usernames']:
                    user_manager.course_register_user(course, u, force=True)
            except:
                logger.error("There was an error while updating the database. Some users may have been unregistered from the course %s",
                             str(r['_id']))
        db_version = 2

    if db_version < 3:
        logger.info("Updating database to db_version 3")
        # Add the grade for all the old submissions
        database.submissions.update({}, {"$set": {"grade": 0.0}}, multi=True)
        database.submissions.update({"result": "success"}, {"$set": {"grade": 100.0}}, multi=True)
        database.user_tasks.update({}, {"$set": {"grade": 0.0}}, multi=True)
        database.user_tasks.update({"succeeded": True}, {"$set": {"grade": 100.0}}, multi=True)
        db_version = 3

    if db_version < 4:
        logger.info("Updating database to db_version 4")
        submissions = database.submissions.find({"$where": "!Array.isArray(this.username)"})
        for submission in submissions:
            submission["username"] = [submission["username"]]
            database.submissions.save(submission)
        db_version = 4

    if db_version < 5:
        logger.info("Updating database to db_version 5")
        database.drop_collection("users")
        database.submissions.update_many({}, {"$set": {"response_type": "html"}})
        db_version = 5

    if db_version < 6:
        logger.info("Updating database to db_version 6")
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
            classrooms[course["_id"]] = {"courseid": course["_id"], "groups": [], "description": "Default classroom", "default": True,
                                         "students": course["students"], "tutors": set([])}

        group_list = list(database.groups.find({}, {'_id': 0}))
        for group in group_list:
            classrooms[group["course_id"]]["groups"].append({"size": group["size"], "students": group["users"]})
            classrooms[group["course_id"]]["tutors"] = classrooms[group["course_id"]]["tutors"].union(group["tutors"])

        for classroom in classrooms.values():
            classroom["tutors"] = list(classroom["tutors"])
            database.classrooms.insert(classroom)

        database.classrooms.create_index([("students", pymongo.ASCENDING)])
        database.classrooms.create_index([("groups.students", pymongo.ASCENDING)])

        db_version = 6

    if db_version < 7:
        logger.info("Updating database to db_version 7")
        database.submissions.update_many({}, {"$set": {"custom": {}}})
        db_version = 7

    if db_version < 8:
        logger.info("Updating database to db_version 8")
        database.classrooms.rename("aggregations")
        db_version = 8

    if db_version < 9:
        logger.info("Updating database to db_version 9")
        user_tasks = list(database.user_tasks.find())

        for user_task in user_tasks:
            username = user_task['username']
            taskid = user_task['taskid']
            courseid = user_task['courseid']

            tasks = list(database.submissions.find(
                {"username": username, "courseid": courseid, "taskid": taskid},
                projection=["_id", "status", "result", "grade", "submitted_on"],
                sort=[('submitted_on', pymongo.DESCENDING)]))

            # Before db v9, the default submission for evaluation was the best
            idx_best = -1
            for idx, val in enumerate(tasks):
                if idx_best == -1 or (val["status"] == "done" and tasks[idx_best]["grade"] < val["grade"]):
                    idx_best = idx

            # If best submission found, update and otherwise set to None
            if idx_best != -1:
                database.user_tasks.update_one({"username": username, "courseid": courseid, "taskid": taskid}, {"$set": {"submissionid": tasks[idx_best]["_id"]}})
            else:
                database.user_tasks.update_one({"username": username, "courseid": courseid, "taskid": taskid},
                                               {"$set": {"submissionid": None}})

        db_version = 9

    # Consistency bug : submissions must have a user task associated
    if db_version < 10:
        logger.info("Updating database to db_version 10")
        triplets = list(database.submissions.aggregate([{"$unwind": "$username"}, {"$group": {"_id": {"username": "$username", "taskid": "$taskid", "courseid": "$courseid"}}}]))
        for triplet in triplets:
            data = triplet['_id']
            user_task = database.user_tasks.find_one(data)
            if not user_task:
                submissions = list(database.submissions.find(data))
                data['tried'] = 0
                data['succeeded'] = False
                data['grade'] = -1
                data['submissionid'] = None
                for submission in submissions:
                    data['tried'] += 1
                    if "result" in submission and submission["result"] == "success":
                        data['succeeded'] = True
                    if "grade" in submission and data['grade'] < submission['grade']:
                        data['grade'] = submission['grade']
                        data['submissionid'] = submission['_id']

                database.user_tasks.insert(data)

        db_version = 10

    # Fix consistency bug in v9 and v10 : crashed submissions could also be set submission
    if db_version < 11:
        logger.info("Updating database to db_version 11")
        user_tasks = list(database.user_tasks.find())

        for user_task in user_tasks:
            username = user_task['username']
            taskid = user_task['taskid']
            courseid = user_task['courseid']

            if user_task["submissionid"] is None:
                tasks = list(database.submissions.find(
                    {"username": username, "courseid": courseid, "taskid": taskid},
                    projection=["_id", "status", "result", "grade", "submitted_on"],
                    sort=[('submitted_on', pymongo.DESCENDING)]))
                if len(tasks) > 0:
                    # No set submission and len(submissions) > 0 should not happen
                    # As update 9 fixed this for successful submissions, all these have crashed, set the first one
                    database.user_tasks.update_one({"username": username, "courseid": courseid, "taskid": taskid},
                                                   {"$set": {"submissionid": tasks[0]["_id"]}})

        db_version = 11

    if db_version < 12:
        logger.info("Updating database to db_version 12")
        database.submissions.create_index([("grade", pymongo.DESCENDING), ("submitted_on", pymongo.DESCENDING)])
        db_version = 12

    if db_version < 13:
        logger.info("Updating database to db_version 13")
        database.nonce.create_index(
            [("timestamp", pymongo.ASCENDING), ("nonce", pymongo.ASCENDING)],
            unique=True
        )
        database.nonce.create_index("expiration", expireAfterSeconds=0)
        db_version = 13

    if db_version < 14:
        logger.info("Updating database to db_version 14")
        ss = database.submissions.find({},{"_id": 1, "input": 1})
        for item in ss:
            try:
                inp = item.get("input", {})
                gridfs_id = None
                if not isinstance(inp, dict): # retrieve from gridfs
                    gridfs_id = inp
                    inp = json.loads(gridfs.get(inp).read().decode('utf8'))

                new_id = gridfs.put(bson.BSON.encode(inp))
                database.submissions.update_one({"_id": item["_id"]}, {"$set": {"input": new_id}})
                if gridfs_id is not None:
                    gridfs.delete(gridfs_id)
            except:
                logger.exception("An exception occured while updating an entry in the DB. You may need to update manually.")
        db_version = 14

    database.db_version.update({}, {"$set": {"db_version": db_version}}, upsert=True)
