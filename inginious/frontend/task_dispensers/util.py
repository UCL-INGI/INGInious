# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from collections import namedtuple
from inginious.common.base import id_checker
from inginious.frontend.accessible_time import AccessibleTime

SectionConfigItem = namedtuple('SectionConfigItem', ['label', 'type', 'default'])

class InvalidTocException(Exception):
    pass


class SectionsList(object):
    """ A list of section for a course structure """

    def __init__(self, structure):
        self._sections = []
        if not all("rank" in section for section in structure):
            raise InvalidTocException(_("No rank for one section"))
        for section in sorted(structure,key=lambda k: k['rank']):
            if "sections_list" in section:
                self._sections.append(NonTerminalSection(section))
            elif "tasks_list" in section:
                self._sections.append(TerminalSection(section))
            else:
                raise InvalidTocException(_("One section don't contain a sections list nor a tasks list"))

    def __iter__(self):
        return iter(self._sections)

    def is_empty(self):
        """
        :return: True if the list is empty false otherwise
        """
        return len(self._sections) == 0

    def get_tasks(self):
        """
        :return: The ordered list of all the tasks in the subsections
        """
        tasks = []
        for section in self._sections:
            tasks += section.get_tasks()
        return tasks

    def add_task(self, taskid, sectionid):
        """
        Add the task in its corresponding section
        :param taskid: the task id of the task
        :param sectionid: the section id of the section
        :return: True is the task has been added false otherwise
        """
        for i, section in enumerate(self._sections):
            if section.get_id() == sectionid and section.is_empty() and not section.is_terminal():
                self._sections[i] = TerminalSection({"id": section.get_id(), "title": section.get_title(),  "tasks_list": {taskid: 0}})
                return True
            elif section.add_task(taskid, sectionid):
                return True
        return False

    def remove_task(self, taskid):
        """
        Remve the task from the structure
        :param taskid: the task id of the task
        """
        for section in self._sections:
            section.remove_task(taskid)

    def get_value_rec(self,taskid,structure,key):
        """
        Returns the value of key for the taskid in the structure if any or None

        The structure can have mutliples sections_list that countains either sections_list or one tasks_list
        The key should be inside one of the tasks_list
        """
        if "sections_list" in structure:
            for section in structure["sections_list"]:
                weight = self.get_value_rec(taskid,section, key)
                if weight is not None:
                    return weight
        elif "tasks_list" in structure:
            if taskid in structure["tasks_list"]:
                return structure[key].get(taskid, None)
        return None

    def get_course_grade_weighted_sum(self, user_tasks, task_list, get_weight):
        """
        Returns the course grade following a weighted sum
        :param user_tasks: the user tasks as in the database
        :param task_list: the list of tasks for a user
        :param get_weight: a function that take a taskid as input and returns the weight for that taskid
        :returns: the value of the grade
        """
        tasks_data = {taskid: {"succeeded": False, "grade": 0.0} for taskid in task_list}
        tasks_score = [0.0, 0.0]

        for taskid in task_list:
            tasks_score[1] += get_weight(taskid)

        for user_task in user_tasks:
            tasks_data[user_task["taskid"]]["succeeded"] = user_task["succeeded"]
            tasks_data[user_task["taskid"]]["grade"] = user_task["grade"]

            weighted_score = user_task["grade"]*get_weight(user_task["taskid"])
            tasks_score[0] += weighted_score

        course_grade = round(tasks_score[0]/tasks_score[1]) if tasks_score[1] > 0 else 0
        return course_grade

    def to_structure(self):
        """
        :return: The structure in YAML format
        """
        return [section.to_structure(rank) for rank, section in enumerate(self._sections)]


class Section(object):
    def __init__(self, structure):
        if "id" in structure and structure["id"] != "":
            self._id = structure["id"]
        else:
            raise InvalidTocException(_("No id for one section"))
        if "title" in structure and structure["title"] != "":
            self._title = structure["title"]
        else:
            raise InvalidTocException(_("No title for one section"))
        self._config = structure["config"] if "config" in structure else {}

    def get_id(self):
        """
        :return: the id of this section
        """
        return self._id

    def get_title(self):
        """
        :return: the title of this section
        """
        return self._title

    def get_config(self):
        """
        :return: the config dict of this section
        """
        return self._config


class NonTerminalSection(Section):
    def __init__(self, structure):
        Section.__init__(self, structure)
        self._sections_list = SectionsList(structure["sections_list"])

    def is_terminal(self):
        return False

    def get_sections_list(self):
        """
        :return: the list of sub-sections of this section
        """
        return self._sections_list

    def is_empty(self):
        """
        :return: True if the section is empty false otherwise
        """
        return self._sections_list.is_empty()

    def get_tasks(self):
        """
        :return: The ordered list of all the tasks in the subsections
        """
        return self._sections_list.get_tasks()

    def add_task(self, taskid, sectionid):
        """
        Add the task in its corresponding section
        :param taskid: the task id of the task
        :param sectionid: the section id of the section
        :return: True is the task has been added false otherwise
        """
        return self._sections_list.add_task(taskid, sectionid)

    def remove_task(self, taskid):
        """
        Remve the task from the structure
        :param taskid: the task id of the task
        """
        self._sections_list.remove_task(taskid)

    def to_structure(self, rank):
        """
        :return: The structure in YAML format
        """
        return {"id": self._id, "rank": rank, "title": self._title, "sections_list": self._sections_list.to_structure()}


class TerminalSection(Section):
    def __init__(self, structure):
        Section.__init__(self, structure)
        if not all(id_checker(id) for id in structure["tasks_list"]):
            raise InvalidTocException(_("One task id contains non alphanumerical characters"))
        self._task_list = [task for task, _ in sorted(structure["tasks_list"].items(), key=lambda x: x[1])]
        self._weights = {}
        if "weights" in structure:
            for taskid,weight in structure["weights"].items():
                if not (type(weight) == float or type(weight) == int):
                    raise InvalidTocException( ("The weight value must be a numeric >= 0 for the task: " + str(taskid)) )
                elif weight < 0:
                    raise InvalidTocException( ("The weight value must be a numeric >= 0 for the task: " + str(taskid)) )
                else:
                    if taskid in structure['tasks_list']:
                        self._weights[taskid] = weight

        self._no_stored_submissions = {}
        if "no_stored_submissions" in structure:
            for taskid,no_stored_submissions in structure["no_stored_submissions"].items():
                if not type(no_stored_submissions) == int:
                    raise InvalidTocException( ("The store submission must be an integer > 1 for the task: " + str(taskid)) )
                elif no_stored_submissions < 0:
                    raise InvalidTocException( ("The store submission must be an integer > 1 for the task: " + str(taskid)) )
            self._no_stored_submissions = structure["no_stored_submissions"]

        self._evaluation_mode = {}
        if "evaluation_mode" in structure:
            for taskid,evaluation_mode in structure["evaluation_mode"].items():
                if evaluation_mode != "best" and evaluation_mode != "last":
                    raise InvalidTocException( ("The evaluation mode must be either best or last for the task: '" + str(taskid)) +"' but is " + str(evaluation_mode) )
            self._evaluation_mode = structure["evaluation_mode"]

        self._submission_limit = {}
        if "submission_limit" in structure:
            for taskid,submission_limit in structure["submission_limit"].items():
                if not type(submission_limit["amount"]) == int or not type(submission_limit["period"]) == int:
                    raise InvalidTocException("Invalid submission limit for task: " + str(taskid))
                elif submission_limit["amount"] < -1 or submission_limit["period"] < -1:
                    raise InvalidTocException("Submission limit values must be higher than or equal to -1 for task: " + str(taskid))
            self._submission_limit = structure["submission_limit"]

        self._group_submission = {}
        if "group_submission" in structure:
            for taskid, group_submisson in structure["group_submission"].items():
                if not type(group_submisson) == bool:
                    raise InvalidTocException("Invalid submission mode for task: " + str(taskid))
            self._group_submission = structure["group_submission"]

        self._categories = {}
        if "categories" in structure:
            for taskid,categorie in structure["categories"].items():
                if "" in categorie:
                    raise InvalidTocException( ("The categorie must have a name for the task: '" + str(taskid)) +"' but is " + str(categorie) )
            self._categories = structure["categories"]

        self._accessible = {}
        if "accessible" in structure:
            for taskid, accessible in structure["accessible"].items():
                try:
                    AccessibleTime(accessible)
                except Exception as message:
                    raise InvalidTocException("Invalid task accessibility ({}) for the task: {}".format(message, taskid))
            self._accessible = structure["accessible"]

    def is_terminal(self):
        return True

    def get_tasks(self):
        """
        :return: The ordered list of all the tasks in the section
        """
        return self._task_list

    def is_empty(self):
        """
        :return: True if the section is empty false otherwise
        """
        return len(self._task_list) == 0

    def add_task(self, taskid, sectionid):
        """
        Add the task in its corresponding section
        :param taskid: the task id of the task
        :param sectionid: the section id of the section
        :return: True is the task has been added false otherwise
        """
        if not id_checker(taskid):
            return False
        if self._id == sectionid and taskid not in self._task_list:
            self._task_list.append(taskid)
            return True
        return False

    def remove_task(self, taskid):
        """
        Remve the task from the list of tasks if present
        :param taskid: the task id of the task
        """
        if taskid in self._task_list:
            self._task_list.remove(taskid)

    def to_structure(self, rank):
        """
        :return: The structure in YAML format
        """
        return {"id": self._id, "rank": rank, "title": self._title,
                "tasks_list": {taskid: rank for rank, taskid in enumerate(self._task_list)},
                "weights": self._weights, "no_stored_submissions": self._no_stored_submissions,
                "submission_limit": self._submission_limit, "group_submission": self._group_submission,
                "evaluation_mode": self._evaluation_mode, "categories": self._categories,
                "accessible": self._accessible}


def check_toc(toc):
    """
    :param toc: the raw content of the table of content
    :return: (True, "Valid TOC") if the toc has a valid format and (False, The error message) otherwise
    """
    try:
        result = SectionsList(toc)
    except Exception as ex:
        return False, str(ex)
    return True, "Valid TOC"
