# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Classes modifying basic tasks, problems and boxes classes """
import gettext

import inginious.common.tasks
from inginious.common.base import id_checker
from inginious.frontend.webapp.parsable_text import ParsableText
from inginious.frontend.webapp.task_problems import DisplayableCodeProblem, DisplayableCodeFileProblem, \
    DisplayableCodeSingleLineProblem, \
    DisplayableMultipleChoiceProblem, DisplayableMatchProblem


class FrontendTask(inginious.common.tasks.Task):
    """ A task that stores additional context information """

    def __init__(self, course, taskid, content, task_fs, hook_manager, task_problem_types=None):
        # We load the descriptor of the task here to allow plugins to modify settings of the task before it is read by the Task constructor
        if not id_checker(taskid):
            raise Exception("Task with invalid id: " + course.get_id() + "/" + taskid)

        task_problem_types = task_problem_types or {
            "code": DisplayableCodeProblem,
            "code-file": DisplayableCodeFileProblem,
            "code-single-line": DisplayableCodeSingleLineProblem,
            "multiple-choice": DisplayableMultipleChoiceProblem,
            "match": DisplayableMatchProblem}

        super(FrontendTask, self).__init__(course, taskid, content, task_fs, hook_manager, task_problem_types)

        # i18n
        translations_fs = self._fs.from_subfolder("$i18n")
        if translations_fs.exists():
            for f in translations_fs.list(folders=False, files=True, recursive=False):
                lang = f[0:len(f) - 3]
                if translations_fs.exists(lang + ".mo"):
                    self._translations[lang] = gettext.GNUTranslations(translations_fs.get_fd(lang + ".mo"))
                else:
                    self._translations[lang] = gettext.NullTranslations()

        self._name = self._data.get('name', 'Task {}'.format(self.get_id()))

        self._context = self._data.get('context', "")

        # Authors
        if isinstance(self._data.get('author'), str):  # verify if author is a string
            self._author = self._data['author']
        else:
            self._author = ""

        # Submission storage
        self._stored_submissions = int(self._data.get("stored_submissions", 0))

        # Default download
        self._evaluate = self._data.get("evaluate", "best")

    def gettext(self, language, *args, **kwargs):
        translation = self._translations.get(language, gettext.NullTranslations())
        return translation.gettext(*args, **kwargs)

    def get_name(self, language):
        """ Returns the name of this task """
        return self.gettext(language, self._name) if self._name else ""

    def get_context(self, language):
        """ Get the context(description) of this task """
        context = self.gettext(language, self._context) if self._context else ""
        vals = self._hook_manager.call_hook('task_context', course=self.get_course(), task=self, default=context)
        return ParsableText(vals[0], "rst") if len(vals) else ParsableText(context, "rst")

    def get_authors(self, language):
        """ Return the list of this task's authors """
        return self.gettext(language, self._author) if self._author else ""

    def adapt_input_for_backend(self, input_data):
        """ Adapt the input from web.py for the inginious.backend """
        for problem in self._problems:
            input_data = problem.adapt_input_for_backend(input_data)
        return input_data

    def get_stored_submissions(self):
        """ Indicates if only the last submission must be stored for the task """
        return self._stored_submissions

    def get_evaluate(self):
        """ Indicates the default download for the task """
        return self._evaluate
