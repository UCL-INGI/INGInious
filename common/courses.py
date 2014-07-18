""" Contains the class Course and utility functions """
from collections import OrderedDict
import json
from os import listdir
from os.path import isfile, join, splitext

from common.base import INGIniousConfiguration, id_checker
import common.tasks


class Course(object):

    """ Represents a course """

    _task_class = common.tasks.Task

    @classmethod
    def get_all_courses(cls):
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
                output[course] = cls(course)
            except:  # todo log the error
                pass
        return output

    def __init__(self, courseid):
        """Constructor. courseid is the name of the .course file"""
        if not id_checker(courseid):
            raise Exception("Course with invalid name: " + courseid)
        self._content = json.load(open(join(INGIniousConfiguration["tasks_directory"], courseid + ".course"), "r"))
        self._id = courseid
        self._tasks_cache = None

    def get_task(self, taskid):
        """ Return the class with name taskid """
        return self._task_class(self, taskid)

    def get_id(self):
        """ Return the _id of this course """
        return self._id

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
                try:
                    output[task] = self.get_task(task)
                except:
                    pass
            output = OrderedDict(sorted(output.items(), key=lambda t: t[1].get_order()))
            self._tasks_cache = output
        return self._tasks_cache
