# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Displyable problems """

from abc import ABCMeta, abstractmethod
from random import shuffle

import web

from common.tasks_problems import BasicProblem, BasicCodeProblem, CodeProblem, CodeSingleLineProblem, MatchProblem, MultipleChoiceProblem, CodeFileProblem
from frontend.custom.tasks_code_boxes import DisplayableInputBox, DisplayableMultilineBox, DisplayableTextBox, DisplayableFileBox


class DisplayableBasicProblem(BasicProblem):

    """Basic problem """
    __metaclass__ = ABCMeta

    def __str__(self):
        """ get the html for this problem """
        return self.show_input()

    def __unicode__(self):
        """ get the html for this problem """
        return self.show_input()

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the backend """
        return input_data

    @abstractmethod
    def show_input(self):
        """ get the html for this problem """
        pass


class DisplayableBasicCodeProblem(BasicCodeProblem, DisplayableBasicProblem):

    """ A basic class to display all BasicCodeProblem derivatives """

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

    def adapt_input_for_backend(self, input_data):
        for box in self._boxes:
            input_data = box.adapt_input_for_backend(input_data)
        return input_data

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


class DisplayableCodeFileProblem(CodeFileProblem, DisplayableBasicCodeProblem):

    """ A displayable code problem """
    pass


class DisplayableMultipleChoiceProblem(MultipleChoiceProblem, DisplayableBasicProblem):

    """ A displayable multiple choice problem """

    def show_input(self):
        """ Show multiple choice problems """
        choices = []
        limit = self._limit
        if limit == 0:
            limit = len(self._choices)  # no limit

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
