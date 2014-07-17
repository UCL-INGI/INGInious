class Task(object):
    def __init__(self,courseId,taskId):
        if not IdChecker(courseId) and not courseId == "":
            raise Exception("Course with invalid id: "+courseId)
        elif not IdChecker(taskId):
            raise Exception("Task with invalid id: "+courseId+"/"+taskId)
        
        try:
            content = json.load(codecs.open(join(INGIniousConfiguration["tasksDirectory"],courseId,taskId+".task"), "r", 'utf-8'), object_pairs_hook=collections.OrderedDict)
        except IOError:
            raise Exception("File do not exists: "+join(INGIniousConfiguration["tasksDirectory"],courseId,taskId+".task"))
        except Exception as inst:
            raise Exception("Error while reading JSON: "+courseId+"/"+taskId+" :\n"+str(inst))
        
        self.initWithData(courseId, taskId, content)
        self.data = content
    
    def initWithData(self,courseId, taskId, data):
        """Checks content of the JSON data and init the Task object"""
        self.course = None
        self.courseId = courseId
        self.taskId = taskId
        
        self.name = data.get('name','Task {}'.format(taskId))
        
        self.context = ParsableText(data.get('context',""),"HTML" if data.get("contextIsHTML",False) else "rst")
        
        self.environment = data.get('environment',None)
            
        #Authors
        if isinstance(data.get('author'), basestring): #verify if author is a string
            self.author = [data['author']]
        elif isinstance(data.get('author'), list): #verify if author is a list
            for author in data['author']:
                if not isinstance(author, basestring): #authors must be strings
                    raise Exception("This task has an invalid author")
            self.author = data['author']
        else:
            self.author = []
        
        #accessible
        self.accessible = AccessibleTime(data.get("accessible",None))
        
        #Order
        self.order = int(data.get('order',-1))
        
        #Response is HTML
        self.responseIsHTML = data.get("responseIsHTML",False)
        
        #Limits
        self.limits = {"time":20, "memory":1024, "disk": 1024}
        if "limits" in data:
            try:
                self.limits['time'] = int(data["limits"].get("time",20))
                self.limits['memory'] = int(data["limits"].get("memory",1024))
                self.limits['disk'] = int(data["limits"].get("disk",1024))
            except:
                raise Exception("Invalid limit")
        
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
        return self.taskId
    def getProblems(self):
        return self.problems
    def getCourseId(self):
        return self.courseId
    def getCourse(self):
        if self.course == None:
            self.course = common.courses.Course(self.courseId)
        return self.course
    def getAuthors(self):
        return self.author
    def getLimits(self):
        return self.limits
    def getResponseType(self):
        return "HTML" if self.responseIsHTML else "rst"
    def getOrder(self):
        return self.order
    def isOpen(self):
        return self.accessible.is_open()
    
    def checkAnswer(self,taskInput):
        """
            Verify the answers in taskInput. Returns four values
            1st: True the input is **currently** valid. (may become invalid after running the code), False else
            2nd: True if the input needs to be run in the VM, False else
            3rd: Main message, as a list (that can be join with \n or <br/> for example)
            4th: Problem specific message, as a dictionnary
        """
        valid = True
        needLaunch = False
        mainMessage = []
        problemMessages = {}
        multipleChoiceErrorCount = 0
        for problem in self.problems:
            pv, pmm, pm, mcec = problem.checkAnswer(taskInput)
            if pv == None:
                needLaunch = True
            elif pv == False:
                valid = False
            if pmm != None:
                mainMessage.append(pmm)
            if pm != None:
                problemMessages[problem.getId()] = pm
            multipleChoiceErrorCount += mcec
        return valid, needLaunch, mainMessage, problemMessages, multipleChoiceErrorCount

import codecs
import collections
import json
from os.path import join

from common.base import INGIniousConfiguration, IdChecker
import common.courses
from common.parsableText import ParsableText
from common.tasks_problems import CreateTaskProblem
from common.accessibleTime import AccessibleTime
