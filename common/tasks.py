""" Task """
from os.path import join
import codecs
import collections
import json

from common.base import INGIniousConfiguration, id_checker
from common.tasks_problems import CodeProblem, CodeSingleLineProblem, MultipleChoiceProblem, MatchProblem, CodeFileProblem


class Task(object):

    """ Contains the data for a task """

    def __init__(self, course, taskid, init_data=None):
        """
            Init the task. course is a Course object, taskid the task id, and init_data is a dictionnary containing the data needed to initialize the Task object.
            If init_data is None, the data will be taken from the course tasks' directory.
        """

        if not id_checker(taskid):
            raise Exception("Task with invalid id: " + course.get_id() + "/" + taskid)

        self._course = course
        self._taskid = taskid

        if init_data is None:
            try:
                self._data = json.load(
                    codecs.open(
                        join(
                            INGIniousConfiguration["tasks_directory"],
                            self._course.get_id(),
                            self._taskid +
                            ".task"),
                        "r",
                        'utf-8'),
                    object_pairs_hook=collections.OrderedDict)
            except IOError:
                raise Exception("File do not exists: " + join(INGIniousConfiguration["tasks_directory"], self._course.get_id(), self._taskid + ".task"))
            except Exception as inst:
                raise Exception("Error while reading JSON: " + self._course.get_id() + "/" + self._taskid + " :\n" + str(inst))
        else:
            self._data = init_data

        self._environment = self._data.get('environment', None)

        #Response is HTML
        self._response_is_html = self._data.get("responseIsHTML", False)

        # Limits
        self._limits = {"time": 20, "memory": 1024, "disk": 1024}
        if "limits" in self._data:
            try:
                self._limits['time'] = int(self._data["limits"].get("time", 20))
                self._limits['memory'] = int(self._data["limits"].get("memory", 1024))
                self._limits['disk'] = int(self._data["limits"].get("disk", 1024))
            except:
                raise Exception("Invalid limit")

        if "problems" not in self._data:
            raise Exception("Tasks must have some problems descriptions")

        # Check all problems
        self._problems = []

        for problemid in self._data['problems']:
            self._problems.append(self._create_task_problem(self, problemid, self._data['problems'][problemid]))

    def input_is_consistent(self, task_input):
        """ Check if an input for a task is consistent. Return true if this is case, false else """
        for problem in self._problems:
            if not problem.input_is_consistent(task_input):
                return False
        return True

    def get_environment(self):
        """ Returns the environment in which the job manager have to launch this task"""
        return self._environment

    def get_id(self):
        """ Get the id of this task """
        return self._taskid

    def get_problems(self):
        """ Get problems contained in this task """
        return self._problems

    def get_course_id(self):
        """ Return the courseid of the course that contains this task """
        return self._course.get_id()

    def get_course(self):
        """ Return the course that contains this task """
        return self._course

    def get_limits(self):
        """ Return the limits of this task """
        return self._limits

    def get_response_type(self):
        """ Returns the method used to parse the output of the task: HTML or rst """
        return "HTML" if self._response_is_html else "rst"

    def check_answer(self, task_input):
        """
            Verify the answers in task_input. Returns four values
            1st: True the input is **currently** valid. (may become invalid after running the code), False else
            2nd: True if the input needs to be run in the VM, False else
            3rd: Main message, as a list (that can be join with \n or <br/> for example)
            4th: Problem specific message, as a dictionnary
        """
        valid = True
        need_launch = False
        main_message = []
        problem_messages = {}
        multiple_choice_error_count = 0
        for problem in self._problems:
            problem_is_valid, problem_main_message, problem_s_messages, problem_mc_error_count = problem.check_answer(task_input)
            if problem_is_valid is None:
                need_launch = True
            elif problem_is_valid == False:
                valid = False
            if problem_main_message is not None:
                main_message.append(problem_main_message)
            if problem_s_messages is not None:
                problem_messages[problem.get_id()] = problem_s_messages
            multiple_choice_error_count += problem_mc_error_count
        return valid, need_launch, main_message, problem_messages, multiple_choice_error_count

    _problem_types = {"code": CodeProblem, "code-single-line": CodeSingleLineProblem, "code-file": CodeFileProblem, "multiple-choice": MultipleChoiceProblem, "match": MatchProblem}

    def _create_task_problem(self, task, problemid, problem_content):
        """Creates a new instance of the right class for a given problem."""
        # Basic checks
        if not id_checker(problemid):
            raise Exception("Invalid problem _id: " + problemid)
        if problem_content.get('type', "") not in self._problem_types:
            raise Exception("Invalid type for problem " + problemid)

        return self._problem_types.get(problem_content.get('type', ""))(task, problemid, problem_content)

    @classmethod
    def add_problem_type(cls, problem_type, problem_class):
        """ add a new problem type """
        cls._problem_types[problem_type] = problem_class

    @classmethod
    def remove_problem_type(cls, problem_type):
        """ delete a problem type """
        del cls._problem_types[problem_type]

    @classmethod
    def remove_problem_types(cls):
        """ delete all problem types """
        cls._problem_types = {}

    @classmethod
    def add_problem_types(cls, problem_type_dict):
        """ add new problem types """
        cls._problem_types.update(problem_type_dict)
