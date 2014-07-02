from os import listdir
from os.path import isfile, join, splitext
from modules.base import tasksDirectory
import json

class Course:
    
    #Returns a table containing courseId=>{name:courseName, admins:[courseAdmins]} pairs.
    @staticmethod
    def GetAllCoursesIds():
        files = [ f for f in listdir(tasksDirectory) if isfile(join(tasksDirectory,f)) and splitext(join(tasksDirectory,f))[1] == ".course"]
        output = {};
        for course in files:
            try:
                content = json.load(open(join(tasksDirectory,course), "r"))
                if "name" in content and "admins" in content and isinstance(content["admins"],list):
                    output[splitext(course)[0]]={"name": content["name"], "admins": content["admins"]}
            except: #todo log the error
                pass
        return output
    
    def __init__(self,courseId):
        if not courseId.isalnum():
            raise Exception("Course with invalid name: "+courseId)
        try:
            content = json.load(open(join(tasksDirectory,courseId+".course"), "r"))
            if "name" in content and "admins" in content and isinstance(content["admins"],list):
                self.id = courseId
                self.name = content['name']
                self.admins = content['admins']
            else:
                raise Exception("Course has an invalid json description: "+courseId)
        except:
            raise Exception("Course do not exists: "+courseId)
        
    def getName(self):
        return self.name
    def getId(self):
        return self.id
    def getAdmins(self):
        return self.admins
    
    def getCourseTasksDirectory(self):
        return join(tasksDirectory,self.id)
    
    def getTasks(self):
        files = [ f for f in listdir(self.getCourseTasksDirectory()) if isfile(join(self.getCourseTasksDirectory(),f)) and splitext(join(self.getCourseTasksDirectory(),f))[1] == ".task"]
        output = {};
        for task in files:
            try:
                content = json.load(open(join(self.getCourseTasksDirectory(),task), "r"))
                try:
                    output[splitext(task)[0]]=content#Task(content)
                except:
                    pass
            except: #todo log the error
                pass
        return output