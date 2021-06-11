# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from collections import namedtuple
from inginious.common.base import id_checker

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
                "tasks_list": {taskid: rank for rank, taskid in enumerate(self._task_list)}}


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
