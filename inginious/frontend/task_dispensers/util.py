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
        for section in structure:
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

    def to_structure(self):
        """
        :return: The structure in YAML format
        """
        return [section.to_structure() for section in self._sections]


class Section(object):
    def __init__(self, structure):
        if "title" in structure and structure["title"] != "":
            self._title = structure["title"]
        else:
            raise InvalidTocException(_("No title for one section"))
        self._config = structure["config"] if "config" in structure else {}

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

    def to_structure(self):
        """
        :return: The structure in YAML format
        """
        return {"title": self._title, "sections_list": self._sections_list.to_structure()}


class TerminalSection(Section):
    def __init__(self, structure):
        Section.__init__(self, structure)
        if not all(id_checker(id) for id in structure["tasks_list"]):
            raise InvalidTocException(_("One task id contains non alphanumerical characters"))
        self._task_list = structure["tasks_list"]

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

    def to_structure(self):
        """
        :return: The structure in YAML format
        """
        return {
            "title": self._title,
            "tasks_list": {taskid: rank for rank, taskid in enumerate(self._task_list)}
        }


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


def parse_tasks_config(data):
    """
    Parse the task settings and modify data to set default values if needed
    :param data: the raw content of the task settings
    """
    for taskid, structure in data.items():

        # Weight
        weight = structure.get("weight", 1)
        if not (type(weight) == float or type(weight) == int):
            raise InvalidTocException("The weight value must be a numeric >= 0 for the task: " + str(taskid))
        elif weight < 0:
            raise InvalidTocException("The weight value must be a numeric >= 0 for the task: " + str(taskid))
        else:
            structure["weight"] = weight

        # Number of stored submission
        no_stored_submissions = structure.get("no_stored_submissions", 0)
        if not type(no_stored_submissions) == int:
            raise InvalidTocException("The store submission must be an integer > 1 for the task: " + str(taskid))
        elif no_stored_submissions < 0:
            raise InvalidTocException("The store submission must be an integer > 1 for the task: " + str(taskid))
        else:
            structure["no_stored_submissions"] = no_stored_submissions

        evaluation_mode = structure.get("evaluation_mode", "best")
        if evaluation_mode != "best" and evaluation_mode != "last":
            raise InvalidTocException("The evaluation mode must be either best or last for the task: '"
                                      + str(taskid)) + "' but is " + str(evaluation_mode)
        structure["evaluation_mode"] = evaluation_mode

        submission_limit = structure.get("submission_limit", {"amount": -1, "period": -1})
        if not type(submission_limit["amount"]) == int or not type(submission_limit["period"]) == int:
            raise InvalidTocException("Invalid submission limit for task: " + str(taskid))
        elif submission_limit["amount"] < -1 or submission_limit["period"] < -1:
            raise InvalidTocException("Submission limit values must be higher than or equal to -1 for task: " + str(taskid))
        structure["submission_limit"] = submission_limit

        group_submission = structure.get("group_submission", False)
        if not type(group_submission) == bool:
            raise InvalidTocException("Invalid submission mode for task: " + str(taskid))
        structure["group_submission"] = group_submission

        categories = structure.get("categories", [])
        if "" in categories:
            raise InvalidTocException("The category must have a name for the task: '"
                                      + str(taskid) + "' but is " + str(categories))
        structure["categories"] = categories

        accessible = structure.get("accessible", False)
        try:
            AccessibleTime(accessible)
        except Exception as message:
            raise InvalidTocException(
                "Invalid task accessibility ({}) for the task: {}".format(message, taskid))
        structure["accessible"] = accessible

def check_task_config(data):
    """

    :param data: the raw content of the task settings
    :return:  (True, '') if the settings are valid or (False, The error message) otherwise
    """
    try:
        parse_tasks_config(data)
        return True, ''
    except Exception as ex:
        return False, str(ex)