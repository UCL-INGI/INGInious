""" Tasks' problems """
from abc import ABCMeta, abstractmethod
from random import shuffle

from common.base import id_checker
from common.parsableText import ParsableText
from common.tasks_code_boxes import InputBox, MultilineBox, TextBox


class BasicProblem(object):

    """Basic problem. *Should not be instanced*"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_type(self):
        """ Returns the type of the problem """
        return None

    @abstractmethod
    def input_is_consistent(self, task_input):
        """ Check if an input for this problem is consistent. Return true if this is case, false else """
        return False

    @abstractmethod
    def check_answer(self, task_input):
        """
            Check the answer. Returns four values:
            the first is either True, False or None, indicating respectively that the answer is valid, invalid, or need to be sent to VM
            the second is the error message assigned to the task, if any (unused for now)
            the third is the error message assigned to this problem, if any
            this fourth is the number of error if this problem is a multiple choice problem. Must be an integer (0)
        """
        return True, None, None, 0

    def get_id(self):
        """ Get the id of this problem """
        return self._id

    def get_task(self):
        """ Get the task containing this problem """
        return self._task

    def get_name(self):
        """ Get the name of this problem """
        return self._name

    def get_header(self):
        """ Get the header of this problem """
        return self._header

    def __init__(self, task, problemid, content):
        if not id_checker(problemid):
            raise Exception("Invalid problem _id: " + problemid)

        self._id = problemid
        self._task = task
        self._name = content['name'] if "name" in content else ""
        self._header = ParsableText((content['header'] if "header" in content else ""), ("HTML" if "headerIsHTML" in content and content["headerIsHTML"] else "rst"))


class MatchProblem(BasicProblem):

    """Display an input box and check that the content is correct"""

    def __init__(self, task, problemid, content):
        BasicProblem.__init__(self, task, problemid, content)
        if not "answer" in content:
            raise Exception("There is no answer in this problem with type==match")
        self._answer = str(content["answer"])

    def get_type(self):
        return "match"

    def input_is_consistent(self, task_input):
        return self.get_id() in task_input

    def check_answer(self, taskInput):
        if taskInput[self.get_id()].strip() == self._answer:
            return True, None, "Correct answer", 0
        else:
            return False, None, "Invalid answer", 0


class BasicCodeProblem(BasicProblem):

    """Basic problem with code input. Do all the job with the backend"""

    def __init__(self, task, problemid, content):
        BasicProblem.__init__(self, task, problemid, content)
        self._boxes = []
        if task.get_environment() is None:
            raise Exception("Environment undefined, but there is a problem with type=code or type=code-single-line")

    @abstractmethod
    def get_type(self):
        return None

    def input_is_consistent(self, task_input):
        for box in self._boxes:
            if not box.input_is_consistent(task_input):
                return False
        return True

    def _create_box(self, boxid, box_content):
        """ Create adequate box """
        if not id_checker(boxid) and not boxid == "":
            raise Exception("Invalid box _id " + boxid)
        if "type" not in box_content:
            raise Exception("Box " + boxid + " does not have a type")
        if box_content["type"] == "multiline":
            return MultilineBox(self, boxid, box_content)
        elif box_content["type"] == "text":
            return TextBox(self, boxid, box_content)
        elif box_content["type"] in ["input-text", "input-mail", "input-decimal", "input-integer"]:
            return InputBox(self, boxid, box_content)
        else:
            raise Exception("Unknow box type " + box_content["type"] + "for box _id " + boxid)

    def check_answer(self, _):
        return None, None, None, 0


class CodeSingleLineProblem(BasicCodeProblem):

    """Code problem with a single line of input"""

    def __init__(self, task, problemid, content):
        BasicCodeProblem.__init__(self, task, problemid, content)
        self._boxes = [self._create_box("", {"type": "input-text"})]

    def get_type(self):
        return "code-single-line"


class CodeProblem(BasicCodeProblem):

    """Code problem"""

    def __init__(self, task, problemid, content):
        BasicCodeProblem.__init__(self, task, problemid, content)
        if "boxes" in content:
            self._boxes = []
            for boxid, box_content in content['boxes'].iteritems():
                if boxid == "":
                    raise Exception("Empty box ids are not allowed")
                self._boxes.append(self._create_box(boxid, box_content))
        else:
            if "language" in content:
                self._boxes = [self._create_box("", {"type": "multiline", "language": content["language"]})]
            else:
                self._boxes = [self._create_box("", {"type": "multiline"})]

    def get_type(self):
        return "code"


class MultipleChoiceProblem(BasicProblem):

    """Multiple choice problems"""

    def __init__(self, task, problemid, content):
        BasicProblem.__init__(self, task, problemid, content)
        self._multiple = content.get("multiple", False)
        if "choices" not in content or not isinstance(content['choices'], list):
            raise Exception("Multiple choice problem " + problemid + " does not have choices or choices are not an array")
        good_choices = []
        bad_choices = []
        for index, choice in enumerate(content["choices"]):
            data = {"index": index}
            if "text" not in choice:
                raise Exception("A choice in " + problemid + " does not have text")
            data['text'] = ParsableText(choice['text'], 'HTML' if choice.get('textIsHTML', False) else 'rst')
            if choice.get('valid', False):
                data['valid'] = True
                good_choices.append(data)
            else:
                data['valid'] = False
                bad_choices.append(data)

        if len(good_choices) == 0:
            raise Exception("Problem " + problemid + " does not have any valid answer")

        self._limit = 0
        if "limit" in content and isinstance(content['limit'], (int, long)) and content['limit'] >= 0 and content['limit'] >= len(good_choices):
            self._limit = content['limit']
        elif "limit" in content:
            raise Exception("Invalid limit in problem " + problemid)

        self._centralize = content.get("centralize", False)

        self._choices = good_choices + bad_choices
        shuffle(self._choices)

    def get_type(self):
        return "multiple-choice"

    def allow_multiple(self):
        """ Returns true if this multiple choice problem allows checking multiple answers """
        return self._multiple

    def get_choice_with_index(self, index):
        """ Return the choice with index=index """
        for entry in self._choices:
            if entry["index"] == index:
                return entry
        return None

    def input_is_consistent(self, task_input):
        if self.get_id() not in task_input:
            return False
        if self._multiple:
            if not isinstance(task_input[self.get_id()], list):
                return False
            if len(task_input[self.get_id()]) == 0:
                return False
            try:  # test conversion to int
                for entry in task_input[self.get_id()]:
                    if self.get_choice_with_index(int(entry)) is None:
                        return False
            except ValueError:
                return False
        else:
            try:  # test conversion to int
                if self.get_choice_with_index(int(task_input[self.get_id()])) is None:
                    return False
            except ValueError:
                return False
        return True

    def check_answer(self, taskInput):
        valid = True
        if self._multiple:
            for choice in self._choices:
                if choice["valid"] and not choice["index"] in taskInput[self.get_id()] and not str(choice["index"]) in taskInput[self.get_id()]:
                    valid = False
        else:
            valid = self.get_choice_with_index(int(taskInput[self.get_id()]))["valid"]
        if not valid:
            if self._centralize:
                return False, None, None, 1
            else:
                return False, None, "Wrong answer. Make sure to select all the valid possibilities" if self._multiple else "Wrong answer", 1
        return True, None, None, 0


def create_task_problem(task, problemid, problem_content):
    """Creates a new instance of the right class for a given problem."""
    # Basic checks
    if not id_checker(problemid):
        raise Exception("Invalid problem _id: " + problemid)
    if "type" not in problem_content or problem_content['type'] not in ["code", "code-single-line", "multiple-choice", "match"]:
        raise Exception("Invalid type for problem " + problemid)

    # If there is code to send, a VM name must be present
    if problem_content['type'] in ["code", "code-single-line"] and task.get_environment() is None:
        raise Exception("Environment undefined, but there is a problem with type=code")

    if problem_content['type'] == "code":
        return CodeProblem(task, problemid, problem_content)
    elif problem_content['type'] == "code-single-line":
        return CodeSingleLineProblem(task, problemid, problem_content)
    elif problem_content['type'] == "multiple-choice":
        return MultipleChoiceProblem(task, problemid, problem_content)
    elif problem_content['type'] == "match":
        return MatchProblem(task, problemid, problem_content)
