# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Babel extractors for INGInious files """

from inginious.common.base import id_checker
from inginious.common.task_file_readers.yaml_reader import TaskYAMLFileReader
from inginious.common.tasks_problems import CodeProblem, CodeSingleLineProblem, MultipleChoiceProblem, MatchProblem, CodeFileProblem


def get_task_problem(self, problemid, problem_content):
    """Creates a new instance of the right class for a given problem."""
    task_problem_types = {"code": CodeProblem, "code-single-line": CodeSingleLineProblem,
                          "code-file": CodeFileProblem, "multiple-choice": MultipleChoiceProblem, "match": MatchProblem}

    # Basic checks
    if not id_checker(problemid):
        raise Exception("Invalid problem _id: " + problemid)
    if problem_content.get('type', "") not in task_problem_types:
        raise Exception("Invalid type for problem " + problemid)

    return task_problem_types.get(problem_content.get('type', ""))(self, problemid, problem_content)


def extract_yaml(fileobj, keywords, comment_tags, options):
    source = fileobj.read().decode(options.get('encoding', 'utf-8'))
    content = TaskYAMLFileReader().task_reader.load(source)
    keys = ["author", "context", "name"]

    return None