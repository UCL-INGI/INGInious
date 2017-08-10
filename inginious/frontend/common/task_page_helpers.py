# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some functions shared by the task pages from the different frontends """
import json

from inginious.common.tasks_code_boxes import FileBox
from inginious.common.tasks_problems import MultipleChoiceProblem, BasicCodeProblem


def submission_to_json(data, debug, reloading=False, replace=False):
    """ Converts a submission to json (keeps only needed fields) """
    tojson = {
        'status': data['status'],
        'result': data.get('result', 'crash'),
        'id': str(data["_id"]),
        'submitted_on': str(data['submitted_on']),
        'grade': str(data.get("grade", 0.0)),
        'replace': replace and not reloading  # Replace the evaluated submission
    }

    if reloading:
        # Set status='ok' because we are reloading an old submission.
        tojson["status"] = 'ok'
        # And also include input
        tojson["input"] = data.get('input', {})

    if "text" in data:
        tojson["text"] = data["text"]
    if "problems" in data:
        tojson["problems"] = data["problems"]

    if debug:
        tojson["debug"] = data

    if data["result"] == "failed":
        tojson["text"] = _("<b>There are some errors in your answer. "
                           "Your score is {score}%</b> {text}").format(score=data["grade"],
                                                                       text=data["text"])
    elif data["result"] == "success":
        tojson["text"] = _("<b>Your answer passed the tests! "
                           "Your score is {score}%</b> {text}").format(score=data["grade"],
                                                                       text=data["text"])
    elif data["result"] == "timeout":
        tojson["text"] = _("<b>Your submission timed out. "
                           "Your score is {score}%</b> {text}").format(score=data["grade"],
                                                                       text=data["text"])
    elif data["result"] == "overflow":
        tojson["text"] = _("<b>Your submission made an overflow. "
                           "Your score is {score}%</b> {text}").format(score=data["grade"],
                                                                       text=data["text"])
    elif data["result"] == "killed":
        tojson["text"] = _("<b>Your submission was killed.</b> {text}").format(text=data["text"])
    else:
        tojson["text"] = _("<b>An internal error occurred. Please retry later. "
                           "If the error persists, send an email to the course "
                           "administrator.</b> {text}").format(text=data["text"])

    return json.dumps(tojson, default=str)


def list_multiple_multiple_choices_and_files(task):
    """ List problems in task that expect and array as input """
    output = {}
    for problem in task.get_problems():
        if isinstance(problem, MultipleChoiceProblem) and problem.allow_multiple():
            output[problem.get_id()] = []
        elif isinstance(problem, BasicCodeProblem):
            for box in problem.get_boxes():
                if isinstance(box, FileBox):
                    output[box.get_complete_id()] = {}
    return output
