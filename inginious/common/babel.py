# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Babel extractors for INGInious files """

from inginious.common import custom_yaml
from inginious.common.tasks_problems import CodeProblem, CodeSingleLineProblem, MultipleChoiceProblem, MatchProblem, FileProblem


def get_strings(content, fields):
    for key, val in fields.items():
        if isinstance(val, dict):
            yield from get_strings(content.get(key, {}), val)
        elif isinstance(val, list):
            for elem in content.get(key, []):
                yield from get_strings(elem, val[0])
        else:
            result = content.get(key, "")
            if result:
                yield result, key


def extract_yaml(fileobj, keywords, comment_tags, options):
    source = fileobj.read().decode(options.get('encoding', 'utf-8'))
    content = custom_yaml.load(source)

    if "task.yaml" in fileobj.name:
        keys = ["author", "context", "name"]
        for key in keys:
            yield 0, "", content.get(key, ""), [key]

        for problem_id, problem_content in content.get("problems").items():
            task_problem_types = {"code": CodeProblem, "code_single_line": CodeSingleLineProblem,
                                  "file": FileProblem, "multiple_choice": MultipleChoiceProblem,
                                  "match": MatchProblem}

            fields = task_problem_types.get(problem_content.get('type', "")).get_text_fields()

            for string, strkey in get_strings(content.get("problems").get(problem_id), fields):
                yield 0, "", string, [key + ", " + problem_id + ", " + strkey]

    elif "course.yaml" in fileobj.name:
        yield 0, "", content.get("name", ""), ["name"]

