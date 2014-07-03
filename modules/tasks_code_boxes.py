from abc import ABCMeta,abstractmethod
from modules.parsableText import ParsableText

#Basic box. Abstract
class BasicBox:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def getType(self):
        return None
    
    @abstractmethod
    def show(self):
        return None
    
    def getProblem(self):
        return self.problem
    
    def getId(self):
        return self.id
    
    def __str__(self):
        return self.show(self)
    
    def __init__(self,problem,boxId,boxData):
        if not boxId.isalnum() and not boxId == "":
            raise Exception("Invalid box id: "+boxId)
        self.id = boxId
        self.problem = problem

#Text box. Simply shows text.
class TextBox(BasicBox):
    def getType(self):
        return "text"
    
    def show(self):
        return self.content
    
    def __init__(self,problem,boxId,boxData):
        BasicBox.__init__(self, problem, boxId, boxData)
        if "content" not in boxData:
            raise Exception("Box id "+boxId+" with type=text do not have content.")
        self.content = ParsableText(boxData['content'], "HTML" if "contentIsHtml" in boxData and boxData["contentIsHtml"] else "rst")

#Input box. Displays a html input object
class InputBox(BasicBox):
    def getType(self):
        return "input"
    
    def show(self):
        return None #TODO
    
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
        return None #TODO
    
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