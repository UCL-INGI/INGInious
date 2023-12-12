# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Factory for loading courses from disk """

from pymongo import ReturnDocument
from datetime import datetime

from inginious.frontend.log import get_course_logger

from inginious.frontend.exceptions import CourseNotFoundException, CourseAlreadyExistsException, TasksetNotFoundException
from inginious.frontend.courses import Course


# remove from pages/utils.py because only used here for the moment
def dict_data_str_to_datetimes(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    if value == "1-01-01 00:00:00":
                        data[key] = datetime.min
                    elif value == "9999-12-31 23:59:59":
                        data[key] = datetime.max
                    else:
                        data[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if (value != "") else None
                except ValueError:
                    pass  # If it's not a valid date string, continue without converting
            else:
                dict_data_str_to_datetimes(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            dict_data_str_to_datetimes(item)
    return data


def change_access_structure(access_data, needs_soft_end=False):
    """
    Transforms old access structure (course access and registration, task access) into new structure.
    ex: "accessible" can be a boolean or a concatenation of start and end dates ("start/end").
        It will be transformed to have this structure:
            "accessible": {"start": ..., "end": ...}
            "registration": {"start": ..., "end": ...}
            "accessibility": {"start": ...,"soft_end": ..., "end": ...}
        When one of the dates is not given in a custom access or always/never accessible, it will be set to a max or min date.
        examples:
            "registration": {"start": "2023-11-24 16:44:56", "end": "2023-11-24 16:44:56"}
            "accessible": {"start": "2023-11-24 16:44:56", "end": "2023-11-24 16:44:56"}
    :param access_data: dict, old access structure
    :param needs_soft_end: bool, True if the new structure needs a soft_end date in the structure
    :return: dict, new access structure
    """

    new_access_data = {"start": None, "end": None}
    # PK pas des objets datetime ? Les datetime seraint manipulés à l'écriture en YAML (et en DB si cette fonction est appelée à l'écriture en DB)


    if isinstance(access_data, bool):
        new_access_data["end"] = "9999-12-31 23:59:59"
        if needs_soft_end:
            new_access_data["soft_end"] = "9999-12-31 23:59:59"
        if access_data:
            new_access_data["start"] = "0001-01-01 00:00:00"
        else:
            new_access_data["start"] = "9999-12-31 23:59:59"


    elif isinstance(access_data, str) and access_data != "":
        dates = access_data.split("/")
        if needs_soft_end:
            new_access_data["start"] = dates[0]
            new_access_data["soft_end"] = dates[1]
            new_access_data["end"] = dates[2]
        else:
            new_access_data["start"] = dates[0]
            new_access_data["end"] = dates[1]

    return new_access_data


class CourseFactory(object):
    """ Load courses from disk """

    def __init__(self, taskset_factory, task_factory, plugin_manager, database):
        self._taskset_factory = taskset_factory
        self._task_factory = task_factory
        self._plugin_manager = plugin_manager
        self._database = database

        self._migrate_legacy_courses()

    def add_task_dispenser(self, task_dispenser):
        """
        :param task_dispenser: TaskDispenser class
        """
        self._taskset_factory.add_task_dispenser(task_dispenser)

    def get_task_dispensers(self):
        """
        Returns the supported task dispensers by this taskset factory
        """
        return self._taskset_factory.get_task_dispensers()

    def get_task_factory(self):
        """
        :return: the associated task factory
        """
        return self._task_factory

    def get_course_descriptor_content(self, courseid):
        return self._database.courses.find_one({"_id": courseid})

    def update_course_descriptor_content(self, courseid, course_content):
        self._database.courses.find_one_and_update({"_id": courseid}, {"$set": course_content})

    def update_course_descriptor_element(self, courseid, key, value):
        self._database.courses.find_one_and_update({"_id": courseid}, {"$set": {key: value}})

    def import_legacy_course(self, database, courseid):
        course_desc = self.get_course_descriptor_content(courseid)
        database.courses.find_one_and_update({"_id": courseid}, {"$set": course_desc}, upsert=True,
                                                      return_document=ReturnDocument.AFTER)

    def create_course(self, courseid, descriptor):
        existing_course = self._database.courses.find_one({"_id": courseid})
        if existing_course:
            raise CourseAlreadyExistsException()

        descriptor["_id"] = courseid
        self._database.courses.insert_one(descriptor)

    def get_course(self, courseid):
        course_desc = self.get_course_descriptor_content(courseid)
        try:
            return Course(courseid, course_desc, self._taskset_factory, self._task_factory, self._plugin_manager, self._database)
        except Exception as e:
            raise CourseNotFoundException()

    def get_all_courses(self):
        course_descriptors = self._database.courses.find({})
        result = {}
        for course_desc in course_descriptors:
            courseid = course_desc["_id"]
            try:
                result[courseid] = Course(courseid, course_desc, self._taskset_factory, self._task_factory, self._plugin_manager, self._database)
            except Exception:
                get_course_logger(courseid).warning("Cannot open course", exc_info=True)

        return result

    def delete_course(self, courseid):
        self._database.courses.delete_one({"_id": courseid})

    def _migrate_legacy_courses(self):
        courseids = []

        existing_courses = self._database.courses.find({})
        for course_descriptor in existing_courses:
            if "tasksetid" not in course_descriptor:
                courseids.append(course_descriptor["_id"])

        for tasksetid, taskset in self._taskset_factory.get_all_tasksets().items():
            if taskset.is_legacy() and not self._database.courses.find_one({"_id": tasksetid}):
                courseids.append(tasksetid)

        # look here for bad accessibilitY structure ??? -> _migrate_legacy_courses detect the courses whithout taskset (taskset id in DB and correct taskset yaml file)
        # I can maybe also checko here if the taskset file has the right structure (task accessibilities).

        # where to check for DB structure ?

        for courseid in courseids:
            get_course_logger(courseid).warning("Trying to migrate legacy course {}.".format(courseid))

            try:
                taskset_descriptor = self._taskset_factory.get_taskset_descriptor_content(courseid)
                cleaned_taskset_descriptor = {
                    "name": taskset_descriptor["name"],
                    "admins": taskset_descriptor.get("admins", []),
                    "description": taskset_descriptor.get( "description", ""),
                }
                if "task_dispenser" in taskset_descriptor:
                    cleaned_taskset_descriptor["task_dispenser"] = taskset_descriptor["task_dispenser"]
                    cleaned_taskset_descriptor["dispenser_data"] = taskset_descriptor.get("dispenser_data", {})
                taskset_descriptor["tasksetid"] = courseid
                taskset_descriptor["admins"] = taskset_descriptor.get("admins", []) + taskset_descriptor.get("tutors", [])
                if "accessible" in taskset_descriptor:
                    taskset_descriptor["accessible"] = change_access_structure(taskset_descriptor["accessible"])
                if "registration" in taskset_descriptor:
                    taskset_descriptor["registration"] = change_access_structure(taskset_descriptor["registration"])

                # here transform task accessibilities ? -> no, it will be done during the migration of the taskset (import_legacy_tasks)
                # task accessibilities are not in the course descriptor, but in the tasks descriptors (task.yaml)

                taskset_descriptor = dict_data_str_to_datetimes(taskset_descriptor)
                #cleaned_taskset_descriptor = dict_data_str_to_datetimes(cleaned_taskset_descriptor)
                self._database.courses.update_one({"_id": courseid}, {"$set": taskset_descriptor}, upsert=True)
                # why not set cleaned_taskset_descriptor ? -> parce qu'on transmet le taskset_descriptor pour l'enregistrer en DB
                self._taskset_factory.update_taskset_descriptor_content(courseid, cleaned_taskset_descriptor)
            except TasksetNotFoundException as e:
                get_course_logger(courseid).warning("No migration from taskset possible for courseid {}.".format(courseid))

