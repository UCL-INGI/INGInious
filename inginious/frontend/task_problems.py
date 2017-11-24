# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Displyable problems """

import gettext
from abc import ABCMeta, abstractmethod
from random import shuffle

from inginious.frontend.tasks_code_boxes import DisplayableInputBox, DisplayableMultilineBox, DisplayableTextBox, \
    DisplayableFileBox

from inginious.common.tasks_problems import BasicProblem, BasicCodeProblem, CodeProblem, CodeSingleLineProblem, \
    MatchProblem, MultipleChoiceProblem, \
    CodeFileProblem
from inginious.frontend.parsable_text import ParsableText


class DisplayableBasicProblem(BasicProblem, metaclass=ABCMeta):
    """Basic problem """

    def get_header(self, language):
        return ParsableText(super(DisplayableBasicProblem, self).get_header(language), "rst", translation=self._translations.get(language, gettext.NullTranslations()))

    @classmethod
    @abstractmethod
    def get_type_name(self, gettext):
        pass

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        return input_data

    @classmethod
    def get_renderer(cls, template_helper):
        """ Get the renderer for this class problem """
        return template_helper.get_renderer(False)

    @abstractmethod
    def show_input(self, template_helper, language):
        """ get the html for this problem """
        pass

    @classmethod
    @abstractmethod
    def show_editbox(cls, template_helper, key):
        """ get the edit box html for this problem """
        pass


class DisplayableBasicCodeProblem(BasicCodeProblem, DisplayableBasicProblem):
    """ A basic class to display all BasicCodeProblem derivatives """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableBasicCodeProblem, self).__init__(task, problemid, content, translations)
        self._box_types = {
            "input-text": DisplayableInputBox,
            "input-decimal": DisplayableInputBox,
            "input-integer": DisplayableInputBox,
            "multiline": DisplayableMultilineBox,
            "text": DisplayableTextBox,
            "file": DisplayableFileBox}


    @classmethod
    @abstractmethod
    def get_type_name(cls, gettext):
        pass

    def adapt_input_for_backend(self, input_data):
        for box in self._boxes:
            input_data = box.adapt_input_for_backend(input_data)
        return input_data

    def show_input(self, template_helper, language):
        """ Show BasicCodeProblem and derivatives """
        output = ""
        for box in self._boxes:
            output += box.show(template_helper, language)
        return output

    @classmethod
    @abstractmethod
    def show_editbox(cls, template_helper, key):
        pass


class DisplayableCodeProblem(CodeProblem, DisplayableBasicCodeProblem):
    """ A basic class to display all BasicCodeProblem derivatives """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableCodeProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("code")

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableBasicCodeProblem.get_renderer(template_helper).course_admin.subproblems.code(key, True)


class DisplayableCodeSingleLineProblem(CodeSingleLineProblem, DisplayableBasicCodeProblem):
    """ A displayable single code line problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableCodeSingleLineProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("single-line code")

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableBasicCodeProblem.get_renderer(template_helper).course_admin.subproblems.code(key, False)


class DisplayableCodeFileProblem(CodeFileProblem, DisplayableCodeProblem):
    """ A displayable code problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableCodeFileProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(self, gettext):
        return gettext("file upload")

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableCodeFileProblem.get_renderer(template_helper).course_admin.subproblems.code_file(key)


class DisplayableMultipleChoiceProblem(MultipleChoiceProblem, DisplayableBasicProblem):
    """ A displayable multiple choice problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableMultipleChoiceProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(self, gettext):
        return gettext("multiple choice")

    def show_input(self, template_helper, language):
        """ Show multiple choice problems """
        choices = []
        limit = self._limit
        if limit == 0:
            limit = len(self._choices)  # no limit

        # Ensure that the choices are random
        # no need to copy...
        shuffle(self._choices)

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
            # need to have ONE valid entry
            for entry in self._choices:
                if not entry['valid'] and limit > 1:
                    choices.append(entry)
                    limit = limit - 1
            for entry in self._choices:
                if entry['valid'] and limit > 0:
                    choices.append(entry)
                    limit = limit - 1

        shuffle(choices)
        return str(DisplayableMultipleChoiceProblem.get_renderer(template_helper).tasks.multiplechoice(
            self.get_id(), self._multiple, choices,
            lambda text: ParsableText(self.gettext(language, text) if text else "", "rst",
                                      translation=self._translations.get(language, gettext.NullTranslations()))))

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableMultipleChoiceProblem.get_renderer(template_helper).course_admin.subproblems.multiple_choice(key)


class DisplayableMatchProblem(MatchProblem, DisplayableBasicProblem):
    """ A displayable match problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableMatchProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(self, gettext):
        return gettext("match")

    def show_input(self, template_helper, language):
        """ Show MatchProblem """
        return str(DisplayableMatchProblem.get_renderer(template_helper).tasks.match(self.get_id()))

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableMatchProblem.get_renderer(template_helper).course_admin.subproblems.match(key)
