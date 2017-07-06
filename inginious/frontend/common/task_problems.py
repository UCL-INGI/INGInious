# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Displyable problems """

from abc import ABCMeta, abstractmethod
from random import shuffle

from inginious.frontend.common.parsable_text import ParsableText
from inginious.common.tasks_problems import BasicProblem, BasicCodeProblem, CodeProblem, CodeSingleLineProblem, MatchProblem, MultipleChoiceProblem, \
    CodeFileProblem, CodeMultipleLanguagesProblem, CodeFileMultipleLanguagesProblem
from inginious.frontend.common.tasks_code_boxes import DisplayableInputBox, DisplayableMultilineBox, DisplayableTextBox, DisplayableFileBox


class DisplayableBasicProblem(BasicProblem, metaclass=ABCMeta):
    """Basic problem """

    def __init__(self, task, problemid, content):
        super(DisplayableBasicProblem, self).__init__(task, problemid, content)
        self._header = ParsableText(self._header, "rst")

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        return input_data

    @abstractmethod
    def show_input(self, renderer):
        """ get the html for this problem """
        pass


class DisplayableBasicCodeProblem(BasicCodeProblem, DisplayableBasicProblem):
    """ A basic class to display all BasicCodeProblem derivatives """

    def __init__(self, task, problemid, content):
        super(DisplayableBasicCodeProblem, self).__init__(task, problemid, content)

    @abstractmethod
    def get_type(self):
        return None

    _box_types = {
        "input-text": DisplayableInputBox,
        "input-decimal": DisplayableInputBox,
        "input-integer": DisplayableInputBox,
        "multiline": DisplayableMultilineBox,
        "text": DisplayableTextBox,
        "file": DisplayableFileBox}

    _available_languages = {
        "java7": "Java 7",
        "java8": "Java 8",
        "python2": "Python 2.7",
        "python3": "Python 3.5",
        "cpp": "C++",
        "cpp11": "C++11",
        "c": "C",
        "c11": "C11"}

    def adapt_input_for_backend(self, input_data):
        for box in self._boxes:
            input_data = box.adapt_input_for_backend(input_data)
        return input_data

    def show_input(self, renderer):
        """ Show BasicCodeProblem and derivatives """
        output = ""
        for box in self._boxes:
            output += box.show(renderer)
        return output


class DisplayableCodeSingleLineProblem(CodeSingleLineProblem, DisplayableBasicCodeProblem):
    """ A displayable single code line problem """

    def __init__(self, task, problemid, content):
        super(DisplayableCodeSingleLineProblem, self).__init__(task, problemid, content)


class DisplayableCodeProblem(CodeProblem, DisplayableBasicCodeProblem):
    """ A displayable code problem """

    def __init__(self, task, problemid, content):
        super(DisplayableCodeProblem, self).__init__(task, problemid, content)

class DisplayableCodeMultipleLanguagesProblem(CodeMultipleLanguagesProblem, DisplayableBasicCodeProblem):
    """ A displayable code multiple language problem """

    def __init__(self, task, problemid, content):
        super(DisplayableCodeMultipleLanguagesProblem, self).__init__(task, problemid, content)

    def show_input(self, renderer):
        allowed_languages = {language: self._available_languages[language] for language in self._languages}
        dropdown_id = self.get_id() + "/language"
        custom_input_id = self.get_id() + "/input"

        standard_code_problem_render = super(DisplayableCodeMultipleLanguagesProblem, self).show_input(renderer)
        multiple_language_render = str(renderer.tasks.multiplelanguage(self.get_id(), dropdown_id, allowed_languages, self.get_id(), self.get_type()))
        tools_render = str(renderer.tasks.tools(self.get_id(), "plain", custom_input_id, self.get_type()))

        return multiple_language_render + standard_code_problem_render + tools_render


class DisplayableCodeFileProblem(CodeFileProblem, DisplayableBasicCodeProblem):
    """ A displayable code problem """

    def __init__(self, task, problemid, content):
        super(DisplayableCodeFileProblem, self).__init__(task, problemid, content)


class DisplayableCodeFileMultipleLanguagesProblem(CodeFileMultipleLanguagesProblem, DisplayableBasicCodeProblem):
    """ A displayable code file problem with multiple languages """

    def __init__(self, task, problemid, content):
        super(DisplayableCodeFileMultipleLanguagesProblem, self).__init__(task, problemid, content)

    def show_input(self, renderer):
        allowed_languages = {language: self._available_languages[language] for language in self._languages}
        dropdown_id = self.get_id() + "/language"
        custom_input_id = self.get_id() + "/input"

        standard_code_file_problem_render = super(DisplayableCodeFileMultipleLanguagesProblem, self).show_input(renderer)
        multiple_language_render = str(renderer.tasks.multiplelanguage(self.get_id(), dropdown_id, allowed_languages, self.get_id(), self.get_type()))
        tools_render = str(renderer.tasks.tools(self.get_id(), "plain", custom_input_id, self.get_type()))

        return multiple_language_render + standard_code_file_problem_render + tools_render


class DisplayableMultipleChoiceProblem(MultipleChoiceProblem, DisplayableBasicProblem):
    """ A displayable multiple choice problem """

    def __init__(self, task, problemid, content):
        super(DisplayableMultipleChoiceProblem, self).__init__(task, problemid, content)

        for choice in self._choices:
            choice["text"] = ParsableText(choice['text'], 'rst')

    def show_input(self, renderer):
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
        return str(renderer.tasks.multiplechoice(self.get_id(), self._multiple, choices))


class DisplayableMatchProblem(MatchProblem, DisplayableBasicProblem):
    """ A displayable match problem """

    def __init__(self, task, problemid, content):
        super(DisplayableMatchProblem, self).__init__(task, problemid, content)

    def show_input(self, renderer):
        """ Show MatchProblem """
        return str(renderer.tasks.match(self.get_id()))
