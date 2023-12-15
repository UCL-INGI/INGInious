# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """

import gettext

from inginious.frontend.environment_types import get_env_type
from inginious.frontend.parsable_text import ParsableText
from inginious.common.base import id_checker
from inginious.frontend.accessible_time import AccessibleTime


def _migrate_from_v_0_6(content):
    """ Migrate a v0.6 task description to a v0.7+ task description, if needed """
    if "environment" in content:
        content["environment_id"] = content["environment"]
        content["environment_type"] = "docker" if content["environment_id"] != "mcq" else "mcq"
        del content["environment"]
        content["environment_parameters"] = {"limits": content.get("limits", {}),
                                             "run_cmd": content.get("run_cmd", ''),
                                             "network_grading": content.get("network_grading", False),
                                             "response_is_html": content.get('responseIsHTML', False)}
    return content


class Task(object):
    """ A task that stores additional context information, specific to the web app """

    def __init__(self, taskset, taskid, content, plugin_manager, task_problem_types):
        # We load the descriptor of the task here to allow plugins to modify settings of the task before it is read by the Task constructor
        if not id_checker(taskid):
            raise Exception("Task with invalid id: " + taskset.get_id() + "/" + taskid)

        content = _migrate_from_v_0_6(content)

        self._taskset = taskset
        self._taskid = taskid
        self._plugin_manager = plugin_manager
        self._data = content

        if "problems" not in self._data:
            raise Exception("Tasks must have some problems descriptions")

        # i18n
        self._translations = {}
        self._taskset_fs = taskset.get_fs()
        self._taskset_fs.ensure_exists()
        self._task_fs = self._taskset_fs.from_subfolder(taskid)
        self._task_fs.ensure_exists()

        self._translations_fs = self._task_fs.from_subfolder("$i18n")

        if not self._translations_fs.exists():
            self._translations_fs = self._task_fs.from_subfolder("student").from_subfolder("$i18n")
        if not self._translations_fs.exists():
            self._translations_fs = self._taskset_fs.from_subfolder("$common").from_subfolder("$i18n")
        if not self._translations_fs.exists():
            self._translations_fs = self._taskset_fs.from_subfolder("$common").from_subfolder(
                "student").from_subfolder("$i18n")

        if self._translations_fs.exists():
            for f in self._translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if self._translations_fs.exists(lang + ".mo"):
                    self._translations[lang] = gettext.GNUTranslations(self._translations_fs.get_fd(lang + ".mo"))
                else:
                    self._translations[lang] = gettext.NullTranslations()

        # Check all problems
        self._problems = []
        for problemid in self._data['problems']:
            self._problems.append(
                self._create_task_problem(problemid, self._data['problems'][problemid], task_problem_types))

        # Env type
        self._environment_id = self._data.get('environment_id', 'default')
        self._environment_type = self._data.get('environment_type', 'unknown')
        self._environment_parameters = self._data.get("environment_parameters", {})

        env_type_obj = get_env_type(self._environment_type)
        if env_type_obj is None:
            raise Exception(_("Environment type {0} is unknown").format(self._environment_type))
        # Ensure that the content of the dictionary is ok
        self._environment_parameters = env_type_obj.check_task_environment_parameters(self._environment_parameters)

        # Name and context
        self._name = self._data.get('name', 'Task {}'.format(self.get_id()))

        self._context = self._data.get('context', "")

        # Authors
        if isinstance(self._data.get('author'), str):  # verify if author is a string
            self._author = self._data['author']
        else:
            self._author = ""

        if isinstance(self._data.get('contact_url'), str):
            self._contact_url = self._data['contact_url']
        else:
            self._contact_url = ""

        # _accessible
        self._accessible = AccessibleTime(self._data.get("accessible", None))
        
        # Input random
        self._input_random = int(self._data.get("input_random", 0))
        
        # Regenerate input random
        self._regenerate_input_random = bool(self._data.get("regenerate_input_random", False))

    def get_translation_obj(self, language):
        return self._translations.get(language, gettext.NullTranslations())

    def gettext(self, language, text):
        return self.get_translation_obj(language).gettext(text) if text else ""

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):
        """ Check if an input for a task is consistent. Return true if this is case, false else """
        for problem in self._problems:
            if not problem.input_is_consistent(task_input, default_allowed_extension, default_max_size):
                return False
        return True

    def get_environment_id(self):
        """ Returns the environment in which the agent have to launch this task"""
        return self._environment_id

    def get_environment_type(self):
        """ Returns the environment type in which the agent have to launch this task"""
        return self._environment_type

    def get_id(self):
        """ Get the id of this task """
        return self._taskid

    def get_problems(self):
        """ Get problems contained in this task """
        return self._problems

    def get_problems_dict(self):
        """ Get problems dict contained in this task """
        return self._data["problems"]

    def get_environment_parameters(self):
        """ Returns the raw environment parameters, which is a dictionnary that is envtype dependent. """
        return self._environment_parameters

    def get_response_type(self):
        """ Returns the method used to parse the output of the task: HTML or rst """
        return "HTML" if self._environment_parameters.get('response_is_html', False) else "rst"

    def get_fs(self):
        """ Returns a FileSystemProvider which points to the folder of this task """
        return self._task_fs

    def get_hook(self):
        """ Returns the hook manager parameter for this task"""
        return self._plugin_manager

    def get_translation_fs(self):
        """ Return the translation_fs parameter for this task"""
        return self._translations_fs

    def _create_task_problem(self, problemid, problem_content, task_problem_types):
        """Creates a new instance of the right class for a given problem."""
        # Basic checks
        if not id_checker(problemid):
            raise Exception("Invalid problem _id: " + problemid)
        if problem_content.get('type', "") not in task_problem_types:
            raise Exception("Invalid type for problem " + problemid)

        return task_problem_types.get(problem_content.get('type', ""))(problemid, problem_content, self._translations, self._task_fs)

    def get_name(self, language):
        """ Returns the name of this task """
        return self.gettext(language, self._name) if self._name else ""

    def get_context(self, language):
        """ Get the context(description) of this task """
        context = self.gettext(language, self._context) if self._context else ""
        vals = self._plugin_manager.call_hook('task_context', task=self, default=context)
        return ParsableText(vals[0], "rst", translation=self.get_translation_obj(language)) if len(vals) \
            else ParsableText(context, "rst", translation=self.get_translation_obj(language))

    def get_authors(self, language):
        """ Return the list of this task's authors """
        return self.gettext(language, self._author) if self._author else ""

    def get_contact_url(self, _language):
        """ Return the contact link format string for this task """
        return self._contact_url or ""

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        for problem in self._problems:
            input_data = problem.adapt_input_for_backend(input_data)
        return input_data
        
    def get_number_input_random(self):
        """ Return the number of random inputs """
        return self._input_random
        
    def regenerate_input_random(self):
        """ Indicates if random inputs should be regenerated """
        return self._regenerate_input_random

    def get_dispenser_settings(self, fields):
        """ Fetch the legacy config fields now used by task dispensers """
        return {field_class.get_id(): field_class.get_value({field_class.get_id(): self._data[field]}) for field, field_class in fields.items() if field in self._data}
