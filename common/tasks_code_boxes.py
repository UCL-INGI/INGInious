""" Boxes for tasks' problems """
from abc import ABCMeta, abstractmethod
import os.path
import re
import sys

from common.base import id_checker, INGIniousConfiguration
from common.parsable_text import ParsableText


class BasicBox(object):

    """ A basic abstract problem box. A box is a small input for a problem. A problem can contain multiple boxes """
    __metaclass__ = ABCMeta

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

    def input_is_consistent(self, task_input):
        """ Check if an input for this box is consistent. Return true if this is case, false else """
        return self.get_complete_id() in task_input

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

    def input_is_consistent(self, task_input):
        # do not call input_is_consistent from BasicBox.
        return True

    def __init__(self, problem, boxid, boxData):
        BasicBox.__init__(self, problem, boxid, boxData)
        if "content" not in boxData:
            raise Exception("Box _id " + boxid + " with type=text do not have content.")
        self._content = ParsableText(boxData['content'], "HTML" if "contentIsHTML" in boxData and boxData["contentIsHTML"] else "rst")


class FileBox(BasicBox):

    """
        File box. Allow to send a file to the backend.
        The input for this box must be a dictionnary, containing two keys:
        ::

            {
                "filename": "thefilename.txt",
                "value": "the content of the file"
            }

    """

    def get_type(self):
        return "file"

    def input_is_consistent(self, taskInput):
        if not BasicBox.input_is_consistent(self, taskInput):
            return False

        try:
            _, ext = os.path.splitext(taskInput[self.get_complete_id()]["filename"])
            if ext not in self._allowed_exts:
                return False

            if sys.getsizeof(taskInput[self.get_complete_id()]["value"]) > self._max_size:
                return False
        except:
            return False
        return True

    def __init__(self, problem, boxid, boxData):
        BasicBox.__init__(self, problem, boxid, boxData)
        self._allowed_exts = boxData.get("allowed_exts", INGIniousConfiguration.get('allowed_file_extensions', None))
        if self._allowed_exts is None:
            self._allowed_exts = [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"]
        self._max_size = boxData.get("max_size", INGIniousConfiguration.get('max_file_size', None))
        if self._max_size is None:
            self._max_size = 1024 * 1024


class InputBox(BasicBox):

    """ Input box. Displays an input object """

    def get_type(self):
        return "input"

    def input_is_consistent(self, taskInput):
        if not BasicBox.input_is_consistent(self, taskInput):
            return False

        if self._max_chars != 0 and len(taskInput[self.get_complete_id()]) > self._max_chars:
            return False

        # do not allow empty answers
        if len(taskInput[self.get_complete_id()]) == 0:
            return False

        if self._input_type == "integer":
            try:
                int(taskInput[self.get_complete_id()])
            except ValueError:
                return False

        if self._input_type == "decimal":
            try:
                float(taskInput[self.get_complete_id()])
            except ValueError:
                return False
        return True

    def __init__(self, problem, boxid, boxData):
        BasicBox.__init__(self, problem, boxid, boxData)
        if boxData["type"] == "input-text":
            self._input_type = "text"
        elif boxData["type"] == "input-integer":
            self._input_type = "integer"
        elif boxData["type"] == "input-decimal":
            self._input_type = "decimal"
        else:
            raise Exception("No such box type " + boxData["type"] + " in box " + boxid)

        if "maxChars" in boxData and isinstance(boxData['maxChars'], (int, long)) and boxData['maxChars'] > 0:
            self._max_chars = boxData['maxChars']
        elif "maxChars" in boxData:
            raise Exception("Invalid maxChars value in box " + boxid)
        else:
            self._max_chars = 0


class MultilineBox(BasicBox):

    """ Multiline Box """

    def get_type(self):
        return "multiline"

    def input_is_consistent(self, taskInput):
        if not BasicBox.input_is_consistent(self, taskInput):
            return False
        if self._max_chars != 0 and len(taskInput[self.get_complete_id()]) > self._max_chars:
            return False
        # do not allow empty answers
        if len(taskInput[self.get_complete_id()]) == 0:
            return False
        return True

    def __init__(self, problem, boxid, boxData):
        BasicBox.__init__(self, problem, boxid, boxData)
        if "maxChars" in boxData and isinstance(boxData['maxChars'], (int, long)) and boxData['maxChars'] > 0:
            self._max_chars = boxData['maxChars']
        elif "maxChars" in boxData:
            raise Exception("Invalid maxChars value in box " + boxid)
        else:
            self._max_chars = 0

        if "lines" in boxData and isinstance(boxData['lines'], (int, long)) and boxData['lines'] > 0:
            self._lines = boxData['lines']
        elif "lines" in boxData:
            raise Exception("Invalid lines value in box " + boxid)
        else:
            self._lines = 8

        if "language" in boxData and re.match(r'[a-z0-9\-_\.]+$', boxData["language"], re.IGNORECASE):
            self._language = boxData["language"]
        elif "language" in boxData:
            raise Exception("Invalid language " + boxData["language"])
        else:
            self._language = "plain"
