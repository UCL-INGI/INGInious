from collections import OrderedDict
import json
from os import listdir
from os.path import isfile, join, splitext

from common.accessibleTime import AccessibleTime
from common.base import INGIniousConfiguration, IdChecker
from common.tasks import Task


# Represents a Course
class Course(object):
    """ Represents a course """
    
    @staticmethod
    def GetAllCourses(noCache=True):
        """Returns a table containing courseId=>Course pairs."""
        files = [ splitext(f)[0] for f in listdir(INGIniousConfiguration["tasksDirectory"]) if isfile(join(INGIniousConfiguration["tasksDirectory"], f)) and splitext(join(INGIniousConfiguration["tasksDirectory"], f))[1] == ".course"]
        output = {};
        for course in files:
            try:
                output[course] = Course(course)
            except:  # todo log the error
                pass
        return output

    def __init__(self, courseId):
        """Constructor. courseId is the name of the .course file"""
        if not IdChecker(courseId):
            raise Exception("Course with invalid name: " + courseId)
        content = json.load(open(join(INGIniousConfiguration["tasksDirectory"], courseId + ".course"), "r"))
        if "name" in content and "admins" in content and isinstance(content["admins"], list):
            self.id = courseId
            self.name = content['name']
            self.admins = content['admins']
            self.tasksCache = None
            self.accessible = AccessibleTime(content.get("accessible",None))
        else:
            raise Exception("Course has an invalid json description: " + courseId)

    def getName(self):
        return self.name
    def getId(self):
        return self.id
    def getAdmins(self):
        return self.admins
    def isOpen(self):
        return self.accessible.is_open()
    
    def getCourseTasksDirectory(self):
        """Return the complete path to the tasks directory of the course"""
        return join(INGIniousConfiguration["tasksDirectory"], self.id)

    def getTasks(self):
        """Get all tasks in this course"""
        if self.tasksCache == None:
            # lists files ending with .task in the right directory, and keep only the taskId
            files = [ splitext(f)[0] for f in listdir(self.getCourseTasksDirectory()) if isfile(join(self.getCourseTasksDirectory(), f)) and splitext(join(self.getCourseTasksDirectory(), f))[1] == ".task"]
            output = {};
            for task in files:
                #try:
                    output[task] = Task(self.getId(), task)
                #except:
                #    pass
            output = OrderedDict(sorted(output.items(), key=lambda t: t[1].getOrder()))
            self.tasksCache = output
        return self.tasksCache
