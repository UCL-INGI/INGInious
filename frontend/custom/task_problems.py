""" Displyable problems """

from abc import ABCMeta, abstractmethod
from random import shuffle

import web

from common.tasks_problems import BasicProblem, BasicCodeProblem, CodeProblem, CodeSingleLineProblem, MatchProblem, MultipleChoiceProblem
from frontend.custom.tasks_code_boxes import DisplayableInputBox, DisplayableMultilineBox, DisplayableTextBox


class DisplayableBasicProblem(BasicProblem):

    """Basic problem """
    __metaclass__ = ABCMeta

    def __str__(self):
        """ get the html for this problem """
        return self.show_input()

    def __unicode__(self):
        """ get the html for this problem """
        return self.show_input()

    @abstractmethod
    def show_input(self):
        """ get the html for this problem """
        pass


class DisplayableBasicCodeProblem(BasicCodeProblem, DisplayableBasicProblem):

    """ A basic class to display all BasicCodeProblem derivatives """

    @abstractmethod
    def get_type(self):
        return None

    _box_types = {"input-text": DisplayableInputBox, "input-decimal": DisplayableInputBox, "input-integer": DisplayableInputBox, "multiline": DisplayableMultilineBox, "text": DisplayableTextBox}

    def show_input(self):
        """ Show BasicCodeProblem and derivatives """
        output = ""
        for box in self._boxes:
            output += box.show()
        return output


class DisplayableCodeSingleLineProblem(CodeSingleLineProblem, DisplayableBasicCodeProblem):

    """ A displayable single code line problem """
    pass


class DisplayableCodeProblem(CodeProblem, DisplayableBasicCodeProblem):

    """ A displayable code problem """
    pass


class DisplayableMultipleChoiceProblem(MultipleChoiceProblem, DisplayableBasicProblem):

    """ A displayable multiple choice problem """

    def show_input(self):
        """ Show multiple choice problems """
        choices = []
        limit = self._limit
        if self._multiple:
            # take only the valid choices in the first pass
            for entry in self._choices:
                if entry['valid']:
                    choices.append(entry)
                    limit = limit - 1
            # take everything else in a second pass
            for entry in self._choices:
                if limit == 0:
                    break
                if not entry['valid']:
                    choices.append(entry)
                    limit = limit - 1
        else:
            # need to have a valid entry
            found_valid = False
            for entry in self._choices:
                if limit == 1 and not found_valid and not entry['valid']:
                    continue
                elif limit == 0:
                    break
                choices.append(entry)
                limit = limit - 1
                if entry['valid']:
                    found_valid = True
        shuffle(choices)
        return str(web.template.render('templates/tasks/').multiplechoice(self.get_id(), self._multiple, choices))


class DisplayableMatchProblem(MatchProblem, DisplayableBasicProblem):

    """ A displayable match problem """

    def show_input(self):
        """ Show MatchProblem """
        return str(web.template.render('templates/tasks/').match(self.get_id()))
