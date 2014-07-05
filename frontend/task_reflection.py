""" Modify tasks utilities classes (from modules common.tasks_code_boxes and common.tasks_problems) to include show functions """

from random import shuffle

import web

from common.tasks_code_boxes import TextBox, InputBox, MultilineBox
from common.tasks_problems import BasicCodeProblem, MultipleChoiceProblem


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
MultipleChoiceProblem.showInput = MultipleChoiceProblemShowInput