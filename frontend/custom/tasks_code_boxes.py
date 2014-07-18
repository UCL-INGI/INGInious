""" Modified boxes """
from abc import ABCMeta, abstractmethod

import web

from common.tasks_code_boxes import TextBox, InputBox, MultilineBox


class DisplayableBox(object):

    """ A basic interface for displayable boxes """
    __metaclass__ = ABCMeta

    def __str__(self):
        """ Get the html to show this box """
        return self.show()

    def __unicode__(self):
        """ Get the html to show this box """
        return self.show()

    @abstractmethod
    def show(self):
        """ Get the html to show this box """
        pass


class DisplayableTextBox(TextBox, DisplayableBox):

    """ A displayable text box """

    def show(self):
        """ Show TextBox """
        return str(web.template.render('templates/tasks/').box_text(self._content.parse()))


class DisplayableInputBox(InputBox, DisplayableBox):

    """ A displayable input box """

    def show(self):
        """ Show InputBox """
        return str(web.template.render('templates/tasks/').box_input(self.get_complete_id(), self._input_type, self._max_chars))


class DisplayableMultilineBox(MultilineBox, DisplayableBox):

    """ A displayable multiline box """

    def show(self):
        """ Show MultilineBox """
        return str(web.template.render('templates/tasks/').box_multiline(self.get_complete_id(), self._lines, self._max_chars, self._language))
