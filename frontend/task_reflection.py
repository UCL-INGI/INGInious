""" Modify tasks utilities classes (from modules common.tasks_code_boxes and common.tasks_problems) to include show functions """

from random import shuffle

import web

from common.tasks_code_boxes import TextBox, InputBox, MultilineBox
from common.tasks_problems import BasicCodeProblem, MultipleChoiceProblem
from common.tasks import Task
from common.courses import Course

#Add show functions to problems' boxes
def TextBoxShow(self):
    return str(web.template.render('templates/tasks/').box_text(self.content.parse()))
TextBox.show = TextBoxShow

def InputBoxShow(self):
    return str(web.template.render('templates/tasks/').box_input(self.getCompleteId(),self.input_type,self.maxChars))
InputBox.show = InputBoxShow

def MultilineBoxShow(self):
    return str(web.template.render('templates/tasks/').box_multiline(self.getCompleteId(),self.lines,self.maxChars,self.language))
MultilineBox.show = MultilineBoxShow

#Add showInput functions to tasks' problems
def BasicCodeProblemShowInput(self):
    output = ""
    for box in self.boxes:
        output += box.show()
    return output
BasicCodeProblem.showInput = BasicCodeProblemShowInput

def MultipleChoiceProblemShowInput(self):
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
            if limit == 1 and not foundValid and not entry['valid']:
                continue
            elif limit == 0:
                break
            choices.append(entry)
            limit = limit-1
            if entry['valid']:
                foundValid = True
    shuffle(choices)
    return str(web.template.render('templates/tasks/').multiplechoice(self.getId(),self.multiple,choices))
MultipleChoiceProblem.showInput = MultipleChoiceProblemShowInput

#Add utilities function to manage submissions from the task class
def getUserStatus(self):
    """ Returns "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet """
    from frontend.base import database 
    import frontend.user as User #insert here to avoid initialisation of session
    task_cache = database.taskstatus.find_one({"username":User.getUsername(),"courseId":self.getCourseId(),"taskId":self.getId()})
    if task_cache == None:
        return "notattempted"
    return "succeeded" if task_cache["succeeded"] else "failed"
Task.getUserStatus = getUserStatus

#Add utilities function to manage submissions from the course class
def getUserCompletionPercentage(self):
    """ Returns the percentage (integer) of completion of this course by the current user """
    from frontend.base import database
    import frontend.user as User #insert here to avoid initialisation of session
    taskIds=[]
    for taskId in self.getTasks():
        taskIds.append(taskId)
    result = database.taskstatus.find({"username":User.getUsername(),"courseId":self.getId(),"taskId":{"$in":taskIds},"succeeded":True}).count()
    return int(result*100/len(taskIds))
Course.getUserCompletionPercentage = getUserCompletionPercentage

def getUserLastSubmissions(self,limit=5):
    """ Returns a given number (default 5) of submissions of task from this course """
    from frontend.base import database
    import frontend.user as User #insert here to avoid initialisation of session
    from frontend.submission_manager import getUserLastSubmissions
    taskIds=[]
    for taskId in self.getTasks():
        taskIds.append(taskId)
    return getUserLastSubmissions({"courseId":self.getId(),"taskId":{"$in":taskIds}},limit)
Course.getUserLastSubmissions = getUserLastSubmissions