from modules.parsableText import ParsableText
from abc import ABCMeta,abstractmethod
from modules.tasks_code_boxes import InputBox, MultilineBox, TextBox
from modules.base import IdChecker
from random import shuffle
import web

class BasicProblem:
    """Basic problem. *Should not be instanced*"""
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def getType(self):
        return None
    @abstractmethod
    def showInput(self):
        return None
    @abstractmethod
    def evalResults(self,formInput):
        return None
    
    def getId(self):
        return self.id
    def getTask(self):
        return self.task
    def getName(self):
        return self.name
    def getHeader(self):
        return self.header
    
    def __init__(self,task,problemId,content):
        if not IdChecker(problemId):
            raise Exception("Invalid problem id: "+problemId)
        if "name" not in content or not isinstance(content['name'], basestring):
            raise Exception("Invalid name for problem "+id)
        if "header" not in content or not isinstance(content['header'], basestring):
            raise Exception("Invalid header for problem "+id)
        
        self.id = problemId
        self.task = task
        self.name = content['name']
        self.header = ParsableText(content['header'],"HTML" if "headerIsHTML" in content and content["headerIsHTML"] else "rst")

class BasicCodeProblem(BasicProblem):
    """Basic problem with code input. Do all the job with the backend"""
    def __init__(self,task,problemId,content):
        BasicProblem.__init__(self, task, problemId, content)
        if task.getEnvironment() == None:
            raise Exception("Environment undefined, but there is a problem with type=code or type=code-single-line")
        
    def showInput(self):
        output = ""
        for box in self.boxes:
            output += box.show()
        return output
    
    def evalResults(self,formInput):
        return "" #TODO 
    
    def createBox(self,boxId,boxContent):
        if not IdChecker(boxId) and not boxId == "":
            raise Exception("Invalid box id "+boxId)
        if "type" not in boxContent:
            raise Exception("Box "+boxId+" does not have a type")
        if boxContent["type"] == "multiline":
            return MultilineBox(self,boxId,boxContent)
        elif boxContent["type"] == "text":
            return TextBox(self,boxId,boxContent)
        elif boxContent["type"] in ["input-text","input-mail","input-decimal","input-integer"]:
            return InputBox(self,boxId,boxContent)
        else:
            raise Exception("Unknow box type "+boxContent["type"]+ "for box id "+boxId)
        

class CodeSingleLineProblem(BasicCodeProblem):
    """Code problem with a single line of input"""
    def __init__(self,task,problemId,content):
        BasicCodeProblem.__init__(self,task,problemId,content)
        self.boxes = [self.createBox("", {"type":"input-text"})]
    def getType(self):
        return "code-single-line"
    
class CodeProblem(BasicCodeProblem):
    """Code problem"""
    def __init__(self,task,problemId,content):
        BasicCodeProblem.__init__(self,task,problemId,content)
        if "boxes" in content:
            self.boxes = []
            for boxId, boxContent in content['boxes'].iteritems():
                self.boxes.append(self.createBox(boxId, boxContent))
        else:
            if "language" in content:
                self.boxes = [self.createBox("", {"type":"multiline","language":content["language"]})]
            else:
                self.boxes = [self.createBox("", {"type":"multiline"})]
    def getType(self):
        return "code"

class MultipleChoiceProblem(BasicProblem):
    """Multiple choice problems"""
    def __init__(self,task,problemId,content):
        BasicProblem.__init__(self,task,problemId,content)
        self.multiple = "multiple" in content and content["multiple"]
        if "choices" not in content or not isinstance(content['choices'], list):
            raise Exception("Multiple choice problem "+ problemId +" does not have choices or choices are not an array")
        goodChoices=[]
        badChoices=[]
        for index, choice in enumerate(content["choices"]):
            data={"index": index}
            if "text" not in choice:
                raise Exception("A choice in "+problemId+" does not have text")
            data['text'] = ParsableText(choice['text'], 'HTML' if "textIsHTML" in choice and choice['textIsHTML'] else 'rst')
            if "valid" in choice and choice['valid']:
                data['valid'] = True
                goodChoices.append(data)
            else:
                data['valid'] = False
                badChoices.append(data)
        
        if len(goodChoices) == 0:
            raise Exception("Problem "+problemId+" does not have any valid answer")
        
        self.limit = 0
        if "limit" in content and isinstance(content['limit'],(int,long)) and content['limit'] >= 0 and content['limit'] >= len(goodChoices):
            self.limit = content['limit']
        elif "limit" in content:
            raise Exception("Invalid limit in problem "+problemId)
        
        self.choices = goodChoices+badChoices
        shuffle(self.choices)
    def getType(self):
        return "multiple-choice"
    def showInput(self):
        choices = []
        limit = self.limit
        if self.multiple:
            #take only the valid choices in the first pass
            for entry in self.choices:
                if entry['valid']:
                    choices.append(entry)
                    limit = limit-1
            #take everything else in a second pass
            for entry in self.choices:
                if limit == 0:
                    break
                if not entry['valid']:
                    choices.append(entry)
                    limit = limit-1
        else:
            #need to have a valid entry
            foundValid = False
            for entry in self.choices:
                if limit == 1 and not foundValid and entry['valid']:
                    continue
                elif limit == 0:
                    break
                choices.append(entry)
                limit = limit-1
                if entry['valid']:
                    foundValid = True
        shuffle(choices)
        return str(web.template.render('templates/tasks/').multiplechoice(self.getId(),self.multiple,choices))
    def evalResults(self,formInput):
        return None #TODO

def CreateTaskProblem(task,problemId,problemContent):
    """Creates a new instance of the right class for a given problem."""
    #Basic checks
    if not IdChecker(problemId):
        raise Exception("Invalid problem id: "+problemId)
    if "type" not in problemContent or problemContent['type'] not in ["code","code-single-line","multiple-choice"]:
        raise Exception("Invalid type for problem "+problemId)
    
    #If there is code to send, a VM name must be present
    if problemContent['type'] in ["code","code-single-line"] and task.getEnvironment() == None:
        raise Exception("Environment undefined, but there is a problem with type=code")
    
    if problemContent['type'] == "code":
        return CodeProblem(task,problemId,problemContent)
    elif problemContent['type'] == "code-single-line":
        return CodeSingleLineProblem(task,problemId,problemContent)
    elif problemContent['type'] == "multiple-choice":
        return MultipleChoiceProblem(task,problemId,problemContent)