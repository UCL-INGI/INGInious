""" Modified boxes """
from abc import ABCMeta, abstractmethod
import json

import web

from common.tasks_code_boxes import TextBox, InputBox, MultilineBox, FileBox


class DisplayableBox(object):

    """ A basic interface for displayable boxes """
    __metaclass__ = ABCMeta

    def __str__(self):
        """ Get the html to show this box """
        return self.show()

    def __unicode__(self):
        """ Get the html to show this box """
        return self.show()

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the backend """
        return input_data

    @abstractmethod
    def show(self):
        """ Get the html to show this box """
        pass


class DisplayableTextBox(TextBox, DisplayableBox):

    """ A displayable text box """

    def show(self):
        """ Show TextBox """
        return str(web.template.render('templates/tasks/').box_text(self._content.parse()))


class DisplayableFileBox(FileBox, DisplayableBox):

    """ A displayable file box """

    def adapt_input_for_backend(self, input_data):
        try:
            input_data[self.get_complete_id()] = {"filename": input_data[self.get_complete_id()].filename, "value": input_data[self.get_complete_id()].value}
        except:
            input_data[self.get_complete_id()] = {}
        return input_data

    def show(self):
        """ Show FileBox """
        return str(web.template.render('templates/tasks/').box_file(self.get_complete_id(), self._max_size, self._allowed_exts, json))


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
