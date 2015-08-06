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
""" Manages the calls to the TC """

import threading
import Queue
import uuid
import pylti.common
from pymongo import ReturnDocument
import time

class LisOutcomeManager(threading.Thread):
    def __init__(self, database, user_manager, course_factory, lti_consumers):
        super(LisOutcomeManager, self).__init__()
        self.daemon = True
        self._database = database
        self._user_manager = user_manager
        self._course_factory = course_factory
        self._lti_consumers = lti_consumers
        self._queue = Queue.Queue()
        self.start()
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        # Load old tasks from the database
        for todo in self._database.lis_outcome_queue.find({}):
            self._add_to_queue(todo)

        try:
            while not self._stopped:
                time.sleep(0.5)
                data = self._queue.get(True, 1000)
                if data is None:
                    continue
                mongo_id, username, courseid, taskid, consumer_key, service_url, result_id, nb_attempt = data

                try:
                    grade = self._user_manager.get_task_grade(self._course_factory.get_task(courseid, taskid), username)
                    grade = grade/100
                    if grade > 1:
                        grade = 1
                    if grade < 0:
                        grade = 0
                except:
                    print "An exception occured while getting a grade in LisOutcomeManager."
                    continue

                try:
                    xml = pylti.common.generate_request_xml(str(uuid.uuid1()), "replaceResult", result_id, grade)
                    if pylti.common.post_message(self._lti_consumers, consumer_key, service_url, xml):
                        self._delete(mongo_id)
                        print "Successfully sent grade to TC: %s" % str(data)
                        continue
                except Exception as e:
                    print "An exception occured while sending a grade to the TC. Exception %s" % str(e)

                if nb_attempt < 5:
                    print "An error occured while sending a grade to the TC. Retrying..."
                    self._increment_attempt(mongo_id)
                else:
                    print "An error occured while sending a grade to the TC. Maximum number of retries reached."
                    self._delete(mongo_id)
        except:
            pass

    def _add_to_queue(self, mongo_entry):
        self._queue.put((mongo_entry["_id"], mongo_entry["username"], mongo_entry["courseid"],
                         mongo_entry["taskid"], mongo_entry["consumer_key"], mongo_entry["service_url"],
                         mongo_entry["result_id"], mongo_entry["nb_attempt"]))

    def add(self, username, courseid, taskid, consumer_key, service_url, result_id):
        """ Add a job in the queue
        :param username:
        :param courseid:
        :param taskid:
        :param consumer_key:
        :param service_url:
        :param result_id:
        """
        search = {"username": username, "courseid": courseid,
                  "taskid": taskid, "service_url": service_url,
                  "consumer_key": consumer_key, "result_id": result_id}

        entry = self._database.lis_outcome_queue.find_one_and_update(search, {"$set":{"nb_attempt": 0}},
                                                                     return_document=ReturnDocument.BEFORE, upsert=True)
        if entry is None: #and it should be
            self._add_to_queue(self._database.lis_outcome_queue.find_one(search))

    def _delete(self, mongo_id):
        """
        Delete an element from the queue in the database
        :param mongo_id:
        :return:
        """
        self._database.lis_outcome_queue.delete_one({"_id": mongo_id})

    def _increment_attempt(self, mongo_id):
        """
        Increment the number of attempt for an entry and
        :param mongo_id:
        :return:
        """
        entry = self._database.lis_outcome_queue.find_one_and_update({"_id": mongo_id}, {"$inc": {"nb_attempt": 1}})

        self._add_to_queue(entry)
