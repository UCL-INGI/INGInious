# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Manages the calls to the TC """
import logging
import threading
import queue
import uuid
import time

# import pylti.common as lti TODO re-add me once PR has been accepted by PyLTI devs
import inginious.common.customlibs.pylti as lti
from pymongo import ReturnDocument


class LisOutcomeManager(threading.Thread):
    def __init__(self, database, user_manager, course_factory, lti_consumers):
        super(LisOutcomeManager, self).__init__()
        self.daemon = True
        self._database = database
        self._user_manager = user_manager
        self._course_factory = course_factory
        self._lti_consumers = lti_consumers
        self._queue = queue.Queue()
        self._stopped = False
        self._logger = logging.getLogger("inginious.lti.outcome_manager")
        self.start()

    def stop(self):
        self._stopped = True

    def run(self):
        # Load old tasks from the database
        for todo in self._database.lis_outcome_queue.find({}):
            self._add_to_queue(todo)

        try:
            while not self._stopped:
                time.sleep(0.5)
                data = self._queue.get()

                mongo_id, username, courseid, taskid, consumer_key, service_url, result_id, nb_attempt = data

                try:
                    grade = self._user_manager.get_task_grade(self._course_factory.get_task(courseid, taskid), username)
                    grade = grade / 100.0
                    if grade > 1:
                        grade = 1
                    if grade < 0:
                        grade = 0
                except Exception:
                    self._logger.error("An exception occurred while getting a grade in LisOutcomeManager.", exc_info=True)
                    continue

                try:
                    xml = lti.generate_request_xml(str(uuid.uuid1()), "replaceResult", result_id, grade)
                    if lti.post_message(self._lti_consumers, consumer_key, service_url, xml):
                        self._delete_in_db(mongo_id)
                        self._logger.debug("Successfully sent grade to TC: %s", str(data))
                        continue
                except Exception:
                    self._logger.error("An exception occurred while sending a grade to the TC.", exc_info=True)

                if nb_attempt < 5:
                    self._logger.debug("An error occurred while sending a grade to the TC. Retrying...")
                    self._increment_attempt(mongo_id)
                else:
                    self._logger.error("An error occurred while sending a grade to the TC. Maximum number of retries reached.")
                    self._delete_in_db(mongo_id)
        except KeyboardInterrupt:
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

        entry = self._database.lis_outcome_queue.find_one_and_update(search, {"$set": {"nb_attempt": 0}},
                                                                     return_document=ReturnDocument.BEFORE, upsert=True)
        if entry is None:  # and it should be
            self._add_to_queue(self._database.lis_outcome_queue.find_one(search))

    def _delete_in_db(self, mongo_id):
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
