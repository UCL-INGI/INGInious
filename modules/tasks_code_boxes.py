from abc import ABCMeta,abstractmethod
from modules.parsableText import ParsableText
from modules.base import IdChecker
import web
import re

#Basic box. Abstract
class BasicBox:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def getType(self):
        return None
    
    @abstractmethod
    def show(self):
        return ""
    
    def getProblem(self):
        return self.problem
    
    def getId(self):
        return self.id
    
    def getCompleteId(self):
        pid = str(self.getProblem().getId())
        bid = str(self.getId())
        if bid != "":
            return pid+"."+bid
        else:
            return pid
    
    def __str__(self):
        return self.show(self)
    
    def __init__(self,problem,boxId,boxData):
        if not IdChecker(boxId) and not boxId == "":
            raise Exception("Invalid box id: "+boxId)
        self.id = boxId
        self.problem = problem

#Text box. Simply shows text.
class TextBox(BasicBox):
    def getType(self):
        return "text"
    
    def show(self):
        return str(web.template.render('templates/tasks/').box_text(self.content.parse()))
    
    def __init__(self,problem,boxId,boxData):
        BasicBox.__init__(self, problem, boxId, boxData)
        if "content" not in boxData:
            raise Exception("Box id "+boxId+" with type=text do not have content.")
        self.content = ParsableText(boxData['content'], "HTML" if "contentIsHTML" in boxData and boxData["contentIsHTML"] else "rst")

#Input box. Displays a html input object
class InputBox(BasicBox):
    def getType(self):
        return "input"
    
    def show(self):
        return str(web.template.render('templates/tasks/').box_input(self.getCompleteId(),self.input_type,self.maxChars))
    
    def __init__(self,problem,boxId,boxData):
        BasicBox.__init__(self, problem, boxId, boxData)
        if boxData["type"] == "input-text": 
            self.input_type = "text"
        elif boxData["type"] == "input-integer":
            self.input_type = "integer"
        elif boxData["type"] == "input-decimal":
            self.input_type = "decimal"
        elif boxData["type"] == "input-mail":
            self.input_type = "mail"
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
    
    def show(self):
        return str(web.template.render('templates/tasks/').box_multiline(self.getCompleteId(),self.lines,self.maxChars,self.language))
    
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