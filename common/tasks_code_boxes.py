from abc import ABCMeta, abstractmethod
import re

from common.base import IdChecker
from common.parsableText import ParsableText


#Basic box. Abstract
class BasicBox:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def getType(self):
        return None
    
    def getProblem(self):
        return self.problem
    
    def getId(self):
        return self.id
    
    def inputIsConsistent(self, taskInput):
        """ Check if an input for this box is consistent. Return true if this is case, false else """
        return self.getCompleteId() in taskInput
    
    def getCompleteId(self):
        """ Returns the complete id of this box. This id is unique among all problems and boxes in an exercice """
        pid = str(self.getProblem().getId())
        bid = str(self.getId())
        if bid != "":
            return pid+"."+bid
        else:
            return pid
    
    def __str__(self):
        return self.show(self)
    
    def __init__(self,problem,boxId,boxData):
        """ Constructor. problem is a BasicProblem (or derivated) instance, boxId a an alphanumeric id and boxData is the data for this box. """
        if not IdChecker(boxId) and not boxId == "":
            raise Exception("Invalid box id: "+boxId)
        self.id = boxId
        self.problem = problem

#Text box. Simply shows text.
class TextBox(BasicBox):
    def getType(self):
        return "text"
    
    def inputIsConsistent(self, taskInput):
        #do not call inputIsConsistent from BasicBox.
        return True
    
    def __init__(self,problem,boxId,boxData):
        BasicBox.__init__(self, problem, boxId, boxData)
        if "content" not in boxData:
            raise Exception("Box id "+boxId+" with type=text do not have content.")
        self.content = ParsableText(boxData['content'], "HTML" if "contentIsHTML" in boxData and boxData["contentIsHTML"] else "rst")

#Input box. Displays a html input object
class InputBox(BasicBox):
    def getType(self):
        return "input"
    
    def inputIsConsistent(self, taskInput):
        if not BasicBox.inputIsConsistent(self, taskInput):
            return False
        
        if self.maxChars != 0 and len(taskInput[self.getCompleteId()]) > self.maxChars:
            return False
        
        #do not allow empty answers
        if len(taskInput[self.getCompleteId()]) == 0:
            return False
        
        if self.input_type == "integer":
            try:
                int(taskInput[self.getCompleteId()])
            except:
                return False
            
        if self.input_type == "decimal":
            try:
                float(taskInput[self.getCompleteId()])
            except:
                return False
        return True
    
    def __init__(self,problem,boxId,boxData):
        BasicBox.__init__(self, problem, boxId, boxData)
        if boxData["type"] == "input-text": 
            self.input_type = "text"
        elif boxData["type"] == "input-integer":
            self.input_type = "integer"
        elif boxData["type"] == "input-decimal":
            self.input_type = "decimal"
        else:
            raise Exception("No such box type "+ boxData["type"] +" in box "+boxId)
        
        if "maxChars" in boxData and isinstance(boxData['maxChars'], (int, long)) and boxData['maxChars'] > 0:
            self.maxChars = boxData['maxChars']
        elif "maxChars" in boxData:
            raise Exception("Invalid maxChars value in box "+boxId)
        else:
            self.maxChars = 0

#Multiline Box. Displays a html textarea object
class MultilineBox(BasicBox):
    def getType(self):
        return "multiline"
    
    def inputIsConsistent(self, taskInput):
        if not BasicBox.inputIsConsistent(self, taskInput):
            return False
        if self.maxChars != 0 and len(taskInput[self.getCompleteId()]) > self.maxChars:
            return False
        #do not allow empty answers
        if len(taskInput[self.getCompleteId()]) == 0:
            return False
        return True
    
    def __init__(self,problem,boxId,boxData):
        BasicBox.__init__(self, problem, boxId, boxData)
        if "maxChars" in boxData and isinstance(boxData['maxChars'], (int, long)) and boxData['maxChars'] > 0:
            self.maxChars = boxData['maxChars']
        elif "maxChars" in boxData:
            raise Exception("Invalid maxChars value in box "+boxId)
        else:
            self.maxChars = 0
            
        if "lines" in boxData and isinstance(boxData['lines'], (int, long)) and boxData['lines'] > 0:
            self.lines = boxData['lines']
        elif "lines" in boxData:
            raise Exception("Invalid lines value in box "+boxId)
        else:
            self.lines = 8
        
        if "language" in boxData and re.match('[a-z0-9\-_\.]+$', boxData["language"], re.IGNORECASE):
            self.language = boxData["language"]
        elif "language" in boxData:
            raise Exception("Invalid language "+boxData["language"])
        else:
            self.language = "plain"