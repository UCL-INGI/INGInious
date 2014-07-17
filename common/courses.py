""" Contains the class Course and utility functions """
from collections import OrderedDict
import json
from os import listdir
from os.path import isfile, join, splitext

from common.accessibleTime import AccessibleTime
from common.base import INGIniousConfiguration, id_checker
from common.tasks import Task


# Represents a Course
class Course(object):

    """ Represents a course """

    @staticmethod
    def get_all_courses():
        """Returns a table containing courseid=>Course pairs."""
        files = [
            splitext(f)[0] for f in listdir(
                INGIniousConfiguration["tasks_directory"]) if isfile(
                join(
                    INGIniousConfiguration["tasks_directory"],
                    f)) and splitext(
                    join(
                        INGIniousConfiguration["tasks_directory"],
                        f))[1] == ".course"]
        output = {}
        for course in files:
            try:
                output[course] = Course(course)
            except:  # todo log the error
                pass
        return output

    def __init__(self, courseid):
        """Constructor. courseid is the name of the .course file"""
        if not id_checker(courseid):
            raise Exception("Course with invalid name: " + courseid)
        content = json.load(open(join(INGIniousConfiguration["tasks_directory"], courseid + ".course"), "r"))
        if "name" in content and "admins" in content and isinstance(content["admins"], list):
            self._id = courseid
            self._name = content['name']
            self._admins = content['admins']
            self._tasks_cache = None
            self._accessible = AccessibleTime(content.get("accessible", None))
        else:
            raise Exception("Course has an invalid json description: " + courseid)

    def get_name(self):
        """ Return the name of this course """
        return self._name

    def get_id(self):
        """ Return the _id of this course """
        return self._id

    def get_admins(self):
        """ Return a list containing the ids of this course """
        return self._admins

    def is_open(self):
        """ Return true if the course is open to students """
        return self._accessible.is_open()

    def get_course_tasks_directory(self):
        """Return the complete path to the tasks directory of the course"""
        return join(INGIniousConfiguration["tasks_directory"], self._id)

    def get_tasks(self):
        """Get all tasks in this course"""
        if self._tasks_cache is None:
            # lists files ending with .task in the right directory, and keep only the taskid
            files = [
                splitext(f)[0] for f in listdir(
                    self.get_course_tasks_directory()) if isfile(
                    join(
                        self.get_course_tasks_directory(),
                        f)) and splitext(
                    join(
                        self.get_course_tasks_directory(),
                        f))[1] == ".task"]
            output = {}
            for task in files:
                # try:
                output[task] = Task(self.get_id(), task)
                # except:
                #    pass
            output = OrderedDict(sorted(output.items(), key=lambda t: t[1].get_order()))
            self._tasks_cache = output
        return self._tasks_cache
