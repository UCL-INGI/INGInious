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
""" Contains the UserData class that helps to manage saved data of a user """
from frontend.base import get_database, add_to_template_globals
from frontend.custom.courses import FrontendCourse


class UserData(object):

    """ Allow to get and to modify _data stored in database for a particular user
            userdata
            {
                "_id":             "gderval",
                "realname":        "Guillaume Derval",
                "email":           "guillaume.derval@student.uclouvain.be",
                "task_tried":      0,
                "task_succeeded":  0,
                "total_tries":     0,
            }

            user_course
            {
                "username":        "gderval",
                "courseid":        "idCourse1",
                "task_tried":      0,
                "task_succeeded":  0,
                "total_tries":     0
            }

            user_task
            {
                "username":        "gderval",
                "courseid":        "idCourse1",
                "taskid":          "idTask1",
                "tried":           0,
                "succeeded":       False
            }
    """

    def __init__(self, username):
        self.username = username
        self._data = None
        self._update_cache()

    def _update_cache(self):
        """ Update internal cache of this object """
        self._data = get_database().users.find_and_modify({"_id": self.username}, {
            "$setOnInsert": {"realname": "", "email": ""}}, upsert=True, new=True)

    def update_basic_informations(self, realname, email):
        """ Update basic informations in the database """
        get_database().users.update(
            {"_id": self.username}, {"$set": {"realname": realname, "email": email}})
        self._update_cache()

    def get_data(self):
        """ Returns data of this user """
        return self._data

    def get_course_data(self, courseid):
        """ Returns data of this user for a specific course."""
        return self.get_course_data_for_users(
            courseid, [
                self.username]).get(
            self.username, None)

    @classmethod
    def get_course_data_for_users(cls, courseid, users=None):
        """
            Returns data of users for a specific course. users is a list of username. If users is none, data from all users will be returned.

            The returned value is a dict:

            {"username": {"task_tried": 0, "total_tries": 0, "task_succeeded": 0}}
        """
        course = FrontendCourse(courseid)
        match = {"courseid": courseid}
        if users is not None:
            match["username"] = {"$in": users}
        # Keep only visibles tasks
        taskids = [
            taskid for taskid,
            task in course.get_tasks().iteritems() if task.is_open()]
        match["taskid"] = {"$in": taskids}

        data = get_database().user_tasks.aggregate(
            [
                {
                    "$match": match}, {
                    "$group": {
                        "_id": "$username", "task_tried": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$ne": [
                                            "$tried", 0]}, 1, 0]}}, "total_tries":{
                            "$sum": "$tried"}, "task_succeeded": {
                                                "$sum": {
                                                    "$cond": [
                                                        "$succeeded", 1, 0]}}}}])
        if data.get('ok', False):
            return_data = {}
            for result in data["result"]:
                result["total_tasks"] = len(taskids)
                username = result["_id"]
                del result["_id"]
                return_data[username] = result
            return return_data
        else:
            return {}

    def get_task_data(self, courseid, taskid):
        """ Returns data of this user for a specific task """
        return get_database().user_tasks.find_one(
            {"username": self.username, "courseid": courseid, "taskid": taskid})

    def view_task(self, courseid, taskid):
        """ Set in the database that the user has viewed this task """
        # Insert a new entry if no one exists
        get_database().user_tasks.update({"username": self.username,
                                          "courseid": courseid,
                                          "taskid": taskid},
                                         {"$setOnInsert": {"username": self.username,
                                                           "courseid": courseid,
                                                           "taskid": taskid,
                                                           "tried": 0,
                                                           "succeeded": False}},
                                         upsert=True)

    @classmethod
    def recompute_user_stats_tasks(cls, usernames=None, courses_tasks=None):
        """
            Recomputes stats for the given tasks. usernames is a list of usernames, and courses_tasks is a dict containing as keys the courseids and as value lists of taskid.
            If courses_tasks is None, then all courses and all tasks will be recomputed. If the value of a key is None, all the tasks of this course will be recomputed.
            If recompute_course is True, recompute_user_stats_courses will be called.
            If recompute_course is True and recompute_user is True, recompute_user_stats_global will be called.

            "username":        "gderval",
            "courseid":        "idCourse1",
            "taskid":          "idTask1",
            "tried":           0,
            "succeeded":       False
        """
        if courses_tasks is None:
            courses_tasks = {
                key: None for key in FrontendCourse.get_all_courses()}
        for course, tasks in courses_tasks.iteritems():
            match = {"courseid": course}
            if usernames is not None:
                match["username"] = {"$in": usernames}
            if tasks is not None:
                match["taskid"] = {"$in": tasks}

            data = get_database().submissions.aggregate([{"$match": match}, {"$group": {
                "_id": {"username": "$username", "courseid": "$courseid", "taskid": "$taskid"},
                "tried": {"$sum": 1},
                "succeeded": {"$max": {"$cond": [{"$eq": ["$result", "success"]}, True, False]}}
            }}])
            if data.get('ok', False):
                for result in data["result"]:
                    get_database().user_courses.update(
                        {
                            "username": result["_id"]["username"],
                            "courseid": result["_id"]["courseid"],
                            "taskid": result["_id"]["taskid"]},
                        {
                            "$set": {
                                "tried": result["tried"],
                                "succeeded": result["succeeded"]}})   
                    

    def update_stats(self, submission, job):
        """ Update stats with a new submission """
        # TODO: replace useless find_and_modify

        # Tasks
        # Insert a new entry if no one exists
        get_database().user_tasks.find_and_modify(
            {
                "username": self.username,
                "courseid": submission["courseid"],
                "taskid": submission["taskid"]},
            {
                "$setOnInsert": {
                    "username": self.username,
                    "courseid": submission["courseid"],
                    "taskid": submission["taskid"],
                    "tried": 0,
                    "succeeded": False}},
            upsert=True)

        # Update inc counter
        get_database().user_tasks.update({"username": self.username, "courseid": submission[
            "courseid"], "taskid": submission["taskid"]}, {"$inc": {"tried": 1}})

        # Set to succeeded if not succeeded yet
        if job["result"] == "success":
            get_database().user_tasks.find_and_modify({"username": self.username, "courseid": submission[
                "courseid"], "taskid": submission["taskid"], "succeeded": False}, {"$set": {"succeeded": True}})
        self._update_cache()

add_to_template_globals("UserData", UserData)
