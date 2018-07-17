# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Displyable problems """

import gettext
import json
from abc import ABCMeta, abstractmethod
from random import Random

from inginious.common.tasks_problems import Problem, CodeProblem, CodeSingleLineProblem, \
    MatchProblem, MultipleChoiceProblem, FileProblem

from inginious.frontend.parsable_text import ParsableText


class DisplayableProblem(Problem, metaclass=ABCMeta):
    """Basic problem """

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
    def show_input(self, template_helper, language, seed):
        """ get the html for this problem """
        pass

    @classmethod
    @abstractmethod
    def show_editbox(cls, template_helper, key):
        """ get the edit box html for this problem """
        pass

    @classmethod
    @abstractmethod
    def show_editbox_templates(cls, template_helper, key):
        return ""


class DisplayableCodeProblem(CodeProblem, DisplayableProblem):
    """ A basic class to display all BasicCodeProblem derivatives """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableCodeProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("code")

    def adapt_input_for_backend(self, input_data):
        return input_data

    def show_input(self, template_helper, language, seed):
        """ Show BasicCodeProblem and derivatives """
        header = ParsableText(self.gettext(language,self._header), "rst",
                              translation=self._translations.get(language, gettext.NullTranslations()))
        return str(DisplayableCodeProblem.get_renderer(template_helper).tasks.code(self.get_id(), header, 8, 0, self._language, self._optional, self._default))

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableCodeProblem.get_renderer(template_helper).course_admin.subproblems.code(key, True)

    @classmethod
    def show_editbox_templates(cls, template_helper, key):
        return ""


class DisplayableCodeSingleLineProblem(CodeSingleLineProblem, DisplayableProblem):
    """ A displayable single code line problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableCodeSingleLineProblem, self).__init__(task, problemid, content, translations)

    def adapt_input_for_backend(self, input_data):
        return input_data

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("single-line code")

    def show_input(self, template_helper, language, seed):
        """ Show InputBox """
        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self._translations.get(language, gettext.NullTranslations()))
        return str(DisplayableCodeSingleLineProblem.get_renderer(template_helper)
                   .tasks.single_line_code(self.get_id(), header, "text", 0, self._optional, self._default))

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableCodeSingleLineProblem.get_renderer(template_helper).course_admin.subproblems.code(key, False)

    @classmethod
    def show_editbox_templates(cls, template_helper, key):
        return ""


class DisplayableFileProblem(FileProblem, DisplayableProblem):
    """ A displayable code problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableFileProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(self, gettext):
        return gettext("file upload")

    def adapt_input_for_backend(self, input_data):
        try:
            input_data[self.get_id()] = {"filename": input_data[self.get_id()].filename,
                                                  "value": input_data[self.get_id()].value}
        except:
            input_data[self.get_id()] = {}
        return input_data

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableFileProblem.get_renderer(template_helper).course_admin.subproblems.file(key)

    def show_input(self, template_helper, language, seed):
        """ Show FileBox """
        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self._translations.get(language, gettext.NullTranslations()))
        return str(DisplayableFileProblem.get_renderer(template_helper).tasks.file(self.get_id(), header, self._max_size, self._allowed_exts))

    @classmethod
    def show_editbox_templates(cls, template_helper, key):
        return ""


class DisplayableMultipleChoiceProblem(MultipleChoiceProblem, DisplayableProblem):
    """ A displayable multiple choice problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableMultipleChoiceProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(self, gettext):
        return gettext("multiple choice")

    def show_input(self, template_helper, language, seed):
        """ Show multiple choice problems """
        choices = []
        limit = self._limit
        if limit == 0:
            limit = len(self._choices)  # no limit

        rand = Random("{}#{}#{}".format(self.get_task().get_id(), self.get_id(), seed))

        # Ensure that the choices are random
        # we *do* need to copy the choices here
        random_order_choices = list(self._choices)
        rand.shuffle(random_order_choices)

        if self._multiple:
            # take only the valid choices in the first pass
            for entry in random_order_choices:
                if entry['valid']:
                    choices.append(entry)
                    limit = limit - 1
            # take everything else in a second pass
            for entry in random_order_choices:
                if limit == 0:
                    break
                if not entry['valid']:
                    choices.append(entry)
                    limit = limit - 1
        else:
            # need to have ONE valid entry
            for entry in random_order_choices:
                if not entry['valid'] and limit > 1:
                    choices.append(entry)
                    limit = limit - 1
            for entry in random_order_choices:
                if entry['valid'] and limit > 0:
                    choices.append(entry)
                    limit = limit - 1

        rand.shuffle(choices)

        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self._translations.get(language, gettext.NullTranslations()))

        return str(DisplayableMultipleChoiceProblem.get_renderer(template_helper).tasks.multiple_choice(
            self.get_id(), header, self._multiple, choices,
            lambda text: ParsableText(self.gettext(language, text) if text else "", "rst",
                                      translation=self._translations.get(language, gettext.NullTranslations()))))

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableMultipleChoiceProblem.get_renderer(template_helper).course_admin.subproblems.multiple_choice(key)

    @classmethod
    def show_editbox_templates(cls, template_helper, key):
        return DisplayableMultipleChoiceProblem.get_renderer(template_helper).course_admin.subproblems.multiple_choice_templates(key)


class DisplayableMatchProblem(MatchProblem, DisplayableProblem):
    """ A displayable match problem """

    def __init__(self, task, problemid, content, translations=None):
        super(DisplayableMatchProblem, self).__init__(task, problemid, content, translations)

    @classmethod
    def get_type_name(self, gettext):
        return gettext("match")

    def show_input(self, template_helper, language, seed):
        """ Show MatchProblem """
        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self._translations.get(language, gettext.NullTranslations()))
        return str(DisplayableMatchProblem.get_renderer(template_helper).tasks.match(self.get_id(), header))

    @classmethod
    def show_editbox(cls, template_helper, key):
        return DisplayableMatchProblem.get_renderer(template_helper).course_admin.subproblems.match(key)

    @classmethod
    def show_editbox_templates(cls, template_helper, key):
        return ""
