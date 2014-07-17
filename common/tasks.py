""" Task """


class Task(object):

    """ Contains the data for a task """

    def __init__(self, courseid, taskid):
        if not id_checker(courseid) and not courseid == "":
            raise Exception("Course with invalid id: " + courseid)
        elif not id_checker(taskid):
            raise Exception("Task with invalid id: " + courseid + "/" + taskid)

        try:
            data = json.load(codecs.open(join(INGIniousConfiguration["tasks_directory"], courseid, taskid + ".task"), "r", 'utf-8'), object_pairs_hook=collections.OrderedDict)
        except IOError:
            raise Exception("File do not exists: " + join(INGIniousConfiguration["tasks_directory"], courseid, taskid + ".task"))
        except Exception as inst:
            raise Exception("Error while reading JSON: " + courseid + "/" + taskid + " :\n" + str(inst))

        self._data = data
        self._course = None
        self._courseid = courseid
        self._taskid = taskid

        self._name = data.get('name', 'Task {}'.format(taskid))

        self._context = ParsableText(data.get('context', ""), "HTML" if data.get("contextIsHTML", False) else "rst")

        self._environment = data.get('environment', None)

        # Authors
        if isinstance(data.get('author'), basestring):  # verify if author is a string
            self._author = [data['author']]
        elif isinstance(data.get('author'), list):  # verify if author is a list
            for author in data['author']:
                if not isinstance(author, basestring):  # authors must be strings
                    raise Exception("This task has an invalid author")
            self._author = data['author']
        else:
            self._author = []

        # _accessible
        self._accessible = AccessibleTime(data.get("_accessible", None))

        # Order
        self._order = int(data.get('order', -1))

        #Response is HTML
        self._response_is_html = data.get("responseIsHTML", False)

        # Limits
        self._limits = {"time": 20, "memory": 1024, "disk": 1024}
        if "limits" in data:
            try:
                self._limits['time'] = int(data["limits"].get("time", 20))
                self._limits['memory'] = int(data["limits"].get("memory", 1024))
                self._limits['disk'] = int(data["limits"].get("disk", 1024))
            except:
                raise Exception("Invalid limit")

        if "problems" not in data:
            raise Exception("Tasks must have some problems descriptions")

        # Check all problems
        self._problems = []

        for problemid in data['problems']:
            self._problems.append(create_task_problem(self, problemid, data['problems'][problemid]))

    def input_is_consistent(self, task_input):
        """ Check if an input for a task is consistent. Return true if this is case, false else """
        for problem in self._problems:
            if not problem.input_is_consistent(task_input):
                return False
        return True

    def get_environment(self):
        """ Returns the environment in which the job manager have to launch this task"""
        return self._environment

    def get_name(self):
        """ Returns the name of this task """
        return self._name

    def get_context(self):
        """ Get the context(description) of this task """
        return self._context

    def get_id(self):
        """ Get the id of this task """
        return self._taskid

    def get_problems(self):
        """ Get problems contained in this task """
        return self._problems

    def get_course_id(self):
        """ Return the courseid of the course that contains this task """
        return self._courseid

    def get_course(self):
        """ Return the course that contains this task """
        if self._course is None:
            self._course = common.courses.Course(self._courseid)
        return self._course

    def get_authors(self):
        """ Return the list of this task's authors """
        return self._author

    def get_limits(self):
        """ Return the limits of this task """
        return self._limits

    def get_response_type(self):
        """ Returns the method used to parse the output of the task: HTML or rst """
        return "HTML" if self._response_is_html else "rst"

    def get_order(self):
        """ Get the position of this task in the course """
        return self._order

    def is_open(self):
        """ Returns if the task is open to students """
        return self._accessible.is_open()

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
            problem_is_valid, problem_main_message, problem_messages, problem_mc_error_count = problem.check_answer(task_input)
            if problem_is_valid is None:
                need_launch = True
            elif problem_is_valid == False:
                valid = False
            if problem_main_message is not None:
                main_message.append(problem_main_message)
            if problem_messages is not None:
                problem_messages[problem.get_id()] = problem_messages
            multiple_choice_error_count += problem_mc_error_count
        return valid, need_launch, main_message, problem_messages, multiple_choice_error_count

import codecs
import collections
import json
from os.path import join

from common.accessibleTime import AccessibleTime
from common.base import INGIniousConfiguration, id_checker
import common.courses
from common.parsableText import ParsableText
from common.tasks_problems import create_task_problem
