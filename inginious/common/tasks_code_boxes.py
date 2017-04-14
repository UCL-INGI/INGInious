# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Boxes for tasks' problems """
from abc import ABCMeta, abstractmethod
import re
import sys

from inginious.common.base import id_checker


class BasicBox(object, metaclass=ABCMeta):
    """ A basic abstract problem box. A box is a small input for a problem. A problem can contain multiple boxes """

    @abstractmethod
    def get_type(self):
        """ Return the type of this box """
        return None

    def get_problem(self):
        """ Return the problem to which this box is linked """
        return self._problem

    def get_id(self):
        """ Return the _id of this box """
        return self._id

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):  # pylint: disable=unused-argument
        """ Check if an input for this box is consistent. Return true if this is case, false else """
        try:
            return self.get_complete_id() in task_input
        except:
            return False

    def get_complete_id(self):
        """ Returns the complete _id of this box. This _id is unique among all problems and boxes in an exercice """
        pid = str(self.get_problem().get_id())
        bid = str(self.get_id())
        if bid != "":
            return pid + "/" + bid
        else:
            return pid

    def __init__(self, problem, boxid, boxdata_):
        """ Constructor. problem is a BasicProblem (or derivated) instance, boxid a an alphanumeric _id and boxdata is the data for this box. """
        if not id_checker(boxid) and not boxid == "":
            raise Exception("Invalid box _id: " + boxid)
        self._id = boxid
        self._problem = problem


class TextBox(BasicBox):
    """Text box. Simply shows text."""

    def get_type(self):
        return "text"

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):
        # do not call input_is_consistent from BasicBox.
        return True

    def __init__(self, problem, boxid, boxData):
        super(TextBox, self).__init__(problem, boxid, boxData)
        if "content" not in boxData:
            raise Exception("Box _id " + boxid + " with type=text do not have content.")
        self._content = boxData['content']


class FileBox(BasicBox):
    """
        File box. Allow to send a file to the inginious.backend.
        The input for this box must be a dictionnary, containing two keys:
        ::

            {
                "filename": "thefilename.txt",
                "value": "the content of the file"
            }

    """

    def get_type(self):
        return "file"

    def input_is_consistent(self, taskInput, default_allowed_extension, default_max_size):
        if not BasicBox.input_is_consistent(self, taskInput, default_allowed_extension, default_max_size):
            return False

        try:
            if not taskInput[self.get_complete_id()]["filename"].endswith(tuple(self._allowed_exts or default_allowed_extension)):
                return False

            if sys.getsizeof(taskInput[self.get_complete_id()]["value"]) > (self._max_size or default_max_size):
                return False
        except:
            return False
        return True

    def __init__(self, problem, boxid, boxData):
        super(FileBox, self).__init__(problem, boxid, boxData)
        self._allowed_exts = boxData.get("allowed_exts", None)
        self._max_size = boxData.get("max_size", None)


class InputBox(BasicBox):
    """ Input box. Displays an input object """

    def get_type(self):
        return "input"

    def input_is_consistent(self, taskInput, default_allowed_extension, default_max_size):
        if not BasicBox.input_is_consistent(self, taskInput, default_allowed_extension, default_max_size):
            return False

        if self._max_chars != 0 and len(taskInput[self.get_complete_id()]) > self._max_chars:
            return False

        # do not allow empty answers
        try:
            if len(taskInput[self.get_complete_id()]) == 0:
                if self._optional:
                    taskInput[self.get_complete_id()] = self._default_value
                else:
                    return False
        except:
            return False

        if self._input_type == "integer":
            try:
                int(taskInput[self.get_complete_id()])
            except:
                return False

        if self._input_type == "decimal":
            try:
                float(taskInput[self.get_complete_id()])
            except:
                return False
        return True

    def __init__(self, problem, boxid, boxData):
        super(InputBox, self).__init__(problem, boxid, boxData)
        if boxData["type"] == "input-text":
            self._input_type = "text"
            self._default_value = ""
        elif boxData["type"] == "input-integer":
            self._input_type = "integer"
            self._default_value = "0"
        elif boxData["type"] == "input-decimal":
            self._input_type = "decimal"
            self._default_value = "0.0"
        else:
            raise Exception("No such box type " + boxData["type"] + " in box " + boxid)

        self._optional = boxData.get("optional", False)

        if "maxChars" in boxData and isinstance(boxData['maxChars'], int) and boxData['maxChars'] > 0:
            self._max_chars = boxData['maxChars']
        elif "maxChars" in boxData:
            raise Exception("Invalid maxChars value in box " + boxid)
        else:
            self._max_chars = 0


class MultilineBox(BasicBox):
    """ Multiline Box """

    def get_type(self):
        return "multiline"

    def input_is_consistent(self, taskInput, default_allowed_extension, default_max_size):
        if not BasicBox.input_is_consistent(self, taskInput, default_allowed_extension, default_max_size):
            return False
        if self._max_chars != 0 and len(taskInput[self.get_complete_id()]) > self._max_chars:
            return False
        # do not allow empty answers
        if len(taskInput[self.get_complete_id()]) == 0:
            if self._optional:
                taskInput[self.get_complete_id()] = ""
            else:
                return False
        return True

    def __init__(self, problem, boxid, boxData):
        super(MultilineBox, self).__init__(problem, boxid, boxData)
        if "maxChars" in boxData and isinstance(boxData['maxChars'], int) and boxData['maxChars'] > 0:
            self._max_chars = boxData['maxChars']
        elif "maxChars" in boxData:
            raise Exception("Invalid maxChars value in box " + boxid)
        else:
            self._max_chars = 0

        self._optional = boxData.get("optional", False)

        if "lines" in boxData and isinstance(boxData['lines'], int) and boxData['lines'] > 0:
            self._lines = boxData['lines']
        elif "lines" in boxData:
            raise Exception("Invalid lines value in box " + boxid)
        else:
            self._lines = 8

        if re.match(r'[a-z0-9\-_\.]+$', boxData.get("language", ""), re.IGNORECASE):
            self._language = boxData.get("language", "")
        elif boxData.get("language", ""):
            raise Exception("Invalid language " + boxData["language"])
        else:
            self._language = "plain"
