# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Some functions shared by the task pages from the different frontends """
import json
from inginious.common.tasks_code_boxes import FileBox
from inginious.common.tasks_problems import MultipleChoiceProblem, BasicCodeProblem


def submission_to_json(data, debug, reloading=False):
    """ Converts a submission to json (keeps only needed fields) """
    tojson = {
        'status': data['status'],
        'result': data.get('result', 'crash'),
        'id': str(data["_id"]),
        'submitted_on': str(data['submitted_on']),
        'grade': str(data.get("grade", 0.0))
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
