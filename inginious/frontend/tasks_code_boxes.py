# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Modified boxes """
import json
from abc import ABCMeta, abstractmethod

from inginious.common.tasks_code_boxes import TextBox, InputBox, MultilineBox, FileBox
from inginious.frontend.parsable_text import ParsableText


class DisplayableBox(object, metaclass=ABCMeta):
    """ A basic interface for displayable boxes """

    def __init__(self, problem, boxid, boxData):
        pass

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        return input_data

    @abstractmethod
    def show(self, renderer, language):
        """ Get the html to show this box """
        pass

    @classmethod
    def get_renderer(cls, template_helper):
        """ Get the renderer for this class problem """
        return template_helper.get_renderer(False)


class DisplayableTextBox(TextBox, DisplayableBox):
    """ A displayable text box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableTextBox, self).__init__(problem, boxid, boxData)

    def show(self, template_helper, language):
        """ Show TextBox """
        return str(DisplayableTextBox.get_renderer(template_helper).tasks.box_text(ParsableText(self._content, "rst", translation=self._translations[language])))


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

    def show(self, template_helper, language):
        """ Show FileBox """
        return str(DisplayableFileBox.get_renderer(template_helper).tasks.box_file(self.get_complete_id(), self._max_size, self._allowed_exts, json))


class DisplayableInputBox(InputBox, DisplayableBox):
    """ A displayable input box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableInputBox, self).__init__(problem, boxid, boxData)

    def show(self, template_helper, language):
        """ Show InputBox """
        return str(DisplayableInputBox.get_renderer(template_helper).tasks.box_input(self.get_complete_id(), self._input_type, self._max_chars, self._optional))


class DisplayableMultilineBox(MultilineBox, DisplayableBox):
    """ A displayable multiline box """

    def __init__(self, problem, boxid, boxData):
        super(DisplayableMultilineBox, self).__init__(problem, boxid, boxData)

    def show(self, template_helper, language):
        """ Show MultilineBox """
        return str(DisplayableMultilineBox.get_renderer(template_helper).tasks.box_multiline(self.get_complete_id(), self._lines, self._max_chars, self._language, self._optional))
