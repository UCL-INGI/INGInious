# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Modified boxes """
from abc import ABCMeta, abstractmethod
import json

from inginious.common.tasks_code_boxes import TextBox, InputBox, MultilineBox, FileBox
from inginious.frontend.common.parsable_text import ParsableText


class DisplayableBox(object, metaclass=ABCMeta):
    """ A basic interface for displayable boxes """

    def __init__(self, problem, boxid, boxData):
        pass

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        return input_data

    @abstractmethod
    def show(self, renderer):
        """ Get the html to show this box """
        pass


class DisplayableTextBox(TextBox, DisplayableBox):
    """ A displayable text box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableTextBox, self).__init__(problem, boxid, boxData)

        self._content = ParsableText(self._content, "rst")

    def show(self, renderer):
        """ Show TextBox """
        return str(renderer.tasks.box_text(self._content))


class DisplayableFileBox(FileBox, DisplayableBox):
    """ A displayable file box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableFileBox, self).__init__(problem, boxid, boxData)

    def adapt_input_for_backend(self, input_data):
        try:
            input_data[self.get_complete_id()] = {"filename": input_data[self.get_complete_id()].filename,
                                                  "value": input_data[self.get_complete_id()].value}
        except:
            input_data[self.get_complete_id()] = {}
        return input_data

    def show(self, renderer):
        """ Show FileBox """
        return str(renderer.tasks.box_file(self.get_complete_id(), self._max_size, self._allowed_exts, json))


class DisplayableInputBox(InputBox, DisplayableBox):
    """ A displayable input box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableInputBox, self).__init__(problem, boxid, boxData)

    def show(self, renderer):
        """ Show InputBox """
        return str(renderer.tasks.box_input(self.get_complete_id(), self._input_type, self._max_chars, self._optional))


class DisplayableMultilineBox(MultilineBox, DisplayableBox):
    """ A displayable multiline box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableMultilineBox, self).__init__(problem, boxid, boxData)

    def show(self, renderer):
        """ Show MultilineBox """
        return str(renderer.tasks.box_multiline(self.get_complete_id(), self._lines, self._max_chars, self._language, self._optional))
