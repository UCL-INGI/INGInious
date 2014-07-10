from abc import ABCMeta, abstractmethod
from random import shuffle

from common.base import IdChecker
from common.parsableText import ParsableText
from common.tasks_code_boxes import InputBox, MultilineBox, TextBox


class BasicProblem:
    """Basic problem. *Should not be instanced*"""
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def getType(self):
        return None
    
    @abstractmethod
    def inputIsConsistent(self, taskInput):
        """ Check if an input for this problem is consistent. Return true if this is case, false else """
        return False
    
    @abstractmethod
    def checkAnswer(self,taskInput):
        """ 
            Check the answer. Returns three values: 
            the first is either True, False or None, indicating respectively that the answer is valid, invalid, or need to be sent to VM
            the second is the error message assigned to the task, if any (unused for now)
            the third is the error message assigned to this problem, if any
        """
        return True, None, None
    
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

class MatchProblem(BasicProblem):
    """Display an input box and check that the content is correct"""
    def __init__(self,task,problemId,content):
        BasicProblem.__init__(self, task, problemId, content)
        if not "answer" in content:
            raise Exception("There is no answer in this problem with type==match")
        self.answer = str(content["answer"])
    def getType(self):
        return "match"
    def inputIsConsistent(self, taskInput):
        return self.getId() in taskInput
    def checkAnswer(self,taskInput):
        if taskInput[self.getId()].strip() == self.answer:
            return True, None, "Correct answer"
        else:
            return False, None, "Invalid answer"
        
class BasicCodeProblem(BasicProblem):
    """Basic problem with code input. Do all the job with the backend"""
    def __init__(self,task,problemId,content):
        BasicProblem.__init__(self, task, problemId, content)
        if task.getEnvironment() == None:
            raise Exception("Environment undefined, but there is a problem with type=code or type=code-single-line")
    
    def inputIsConsistent(self, taskInput):
        for box in self.boxes:
            if not box.inputIsConsistent(taskInput):
                return False
        return True
    
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
    
    def checkAnswer(self,inputData):
        return None, None, None
        

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
                if boxId == "":
                    raise Exception("Empty box ids are not allowed")
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
    
    def allowMultiple(self):
        return self.multiple
    
    def getChoiceWithIndex(self,index):
        for entry in self.choices:
            if entry["index"] == index:
                return entry
        return None
    
    def inputIsConsistent(self, taskInput):
        if self.getId() not in taskInput:
            return False
        if self.multiple:
            if not isinstance(taskInput[self.getId()], list):
                return False
            if len(taskInput[self.getId()]) == 0:
                return False
            try: #test conversion to int
                for entry in taskInput[self.getId()]:
                    if self.getChoiceWithIndex(int(entry)) == None:
                        return False
            except:
                return False
        else:
            try: #test conversion to int
                if self.getChoiceWithIndex(int(taskInput[self.getId()])) == None:
                    return False
            except:
                return False
        return True
    
    def checkAnswer(self,taskInput):
        valid = True
        if self.multiple:
            for choice in self.choices:
                if choice["valid"] and not choice["index"] in taskInput[self.getId()] and not str(choice["index"]) in taskInput[self.getId()]:
                    valid = False
        else:
            valid = self.getChoiceWithIndex(int(taskInput[self.getId()]))["valid"]
        if not valid:
            return False, None, "Wrong answer. Make sure to select all the valid possibilities" if self.multiple else "Wrong answer"
        return True, None, None

def CreateTaskProblem(task,problemId,problemContent):
    """Creates a new instance of the right class for a given problem."""
    #Basic checks
    if not IdChecker(problemId):
        raise Exception("Invalid problem id: "+problemId)
    if "type" not in problemContent or problemContent['type'] not in ["code","code-single-line","multiple-choice","match"]:
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
    elif problemContent['type'] == "match":
        return MatchProblem(task,problemId,problemContent)