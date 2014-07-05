class Task:
    def __init__(self,courseId,taskId):
        if not IdChecker(courseId):
            raise Exception("Course with invalid id: "+courseId)
        elif not IdChecker(taskId):
            raise Exception("Task with invalid id: "+courseId+"/"+taskId)
        
        try:
            content = json.load(open(join(tasksDirectory,courseId,taskId+".task"), "r"), object_pairs_hook=collections.OrderedDict)
        except:
            raise Exception("Task do not exists: "+courseId+"/"+taskId)
        
        self.initWithData(courseId, taskId, content)
    
    def initWithData(self,courseId, taskId, data):
        """Checks content of the JSON data and init the Task object"""
        self.course = None
        self.courseId = courseId
        self.taskId = taskId
        
        if "name" not in data:
            raise Exception("Tasks must have a name: "+taskId)
        self.name = data['name']
        
        if "context" not in data:
            raise Exception("Tasks must have a context: "+taskId)
        self.context = ParsableText(data['context'],"HTML" if "contextIsHTML" in data and data["contextIsHTML"] else "rst")
        
        if "environment" in data:
            self.environment = data['environment']
        else:
            self.environment = None
        if "taskfs" in data:
            self.taskfs = data['taskfs']
        else:
            self.taskfs = None
            
        #Check integrity
        if (self.environment == None and self.taskfs != None) or (self.environment != None and self.taskfs == None):
            raise Exception("Task have to contain either both of 'environment' and 'taskfs' or none of them.")
        
        #Authors
        if "author" in data and isinstance(data['author'], basestring): #verify if author is a string
            self.author = [data['author']]
        elif "author" in data and isinstance(data['author'], list): #verify if author is a list
            for author in data['author']:
                if not isinstance(author, basestring): #authors must be strings
                    raise Exception("This task has an invalid author")
            self.author = data['author']
        else:
            self.author = []
        
        #Limits
        self.limits = {"time":20, "memory":1024, "disk": 1024, "output": 1024}
        if "limits" in data:
            #Check time
            if "time" in data["limits"] and isinstance(data['limits']['time'], (int)):
                self.limits['time'] = data['limits']['time']
            elif "time" in data["limits"]:
                raise Exception("Invalid time limit")
            
            #Check memory
            if "memory" in data["limits"] and isinstance(data['limits']['memory'], (int)):
                self.limits['memory'] = data['limits']['memory']
            elif "memory" in data["limits"]:
                raise Exception("Invalid memory limit")
            
            #Check disk
            if "disk" in data["limits"] and isinstance(data['limits']['disk'], (int)):
                self.limits['disk'] = data['limits']['disk']
            elif "disk" in data["limits"]:
                raise Exception("Invalid disk limit")
            
            #Check output
            if "output" in data["limits"] and isinstance(data['limits']['output'], (int)):
                self.limits['output'] = data['limits']['output']
            elif "output" in data["limits"]:
                raise Exception("Invalid output limit")
        
        if "problems" not in data:
            raise Exception("Tasks must have some problems descriptions")
        
        #Check all problems
        self.problems = []
        
        for problemId in data['problems']:
            self.problems.append(CreateTaskProblem(self,problemId,data['problems'][problemId]))

    def inputIsConsistent(self, taskInput):
        """ Check if an input for a task is consistent. Return true if this is case, false else """
        for problem in self.problems:
            if not problem.inputIsConsistent(taskInput):
                return False
        return True
    
    def getEnvironment(self):
        return self.environment
    def getName(self):
        return self.name
    def getContext(self):
        return self.context
    def getId(self):
        return self.courseId
    def getProblems(self):
        return self.problems
    def getCourse(self):
        if self.course == None:
            self.course = common.courses.Course(self.courseId)
        return self.course
    
import collections
import json
from os.path import join

from common.base import tasksDirectory, IdChecker
import common.courses
from common.parsableText import ParsableText
from common.tasks_problems import CreateTaskProblem


