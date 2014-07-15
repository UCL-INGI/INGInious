import json
from os import listdir
from os.path import isfile, join, splitext

from common.base import INGIniousConfiguration, IdChecker
from common.tasks import Task
from collections import OrderedDict

# Represents a Course
class Course:
    """ Represents a course """
    courseCache = None

    @staticmethod
    def GetAllCourses():
        """Returns a table containing courseId=>{name:courseName, admins:[courseAdmins]} pairs."""
        if Course.courseCache == None:
            files = [ f for f in listdir(INGIniousConfiguration["tasksDirectory"]) if isfile(join(INGIniousConfiguration["tasksDirectory"], f)) and splitext(join(INGIniousConfiguration["tasksDirectory"], f))[1] == ".course"]
            output = {};
            for course in files:
                try:
                    output[splitext(course)[0]] = Course(splitext(course)[0])
                except:  # todo log the error
                    pass
            Course.courseCache = output
        return Course.courseCache

    def __init__(self, courseId):
        """Constructor. courseId is the name of the .course file"""
        if not IdChecker(courseId):
            raise Exception("Course with invalid name: " + courseId)
        try:
            content = json.load(open(join(INGIniousConfiguration["tasksDirectory"], courseId + ".course"), "r"))
            if "name" in content and "admins" in content and isinstance(content["admins"], list):
                self.id = courseId
                self.name = content['name']
                self.admins = content['admins']
                self.tasksCache = None
            else:
                raise Exception("Course has an invalid json description: " + courseId)
        except:
            raise Exception("Course do not exists: " + courseId)

    def getName(self):
        return self.name
    def getId(self):
        return self.id
    def getAdmins(self):
        return self.admins

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
