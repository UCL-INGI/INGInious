# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import json

def load_feedback():
    """ Open existing feedback file """
    result = {}
    if os.path.exists('/.__output/__feedback.json'):
        f = open('/.__output/__feedback.json', 'r')
        cont = f.read()
        f.close()
    else:
        cont = '{}'
    try:
        result = json.loads(cont)
    except ValueError, e:
        result = {"result":"crash", "text":"Feedback file has been modified by user !"}
    return result

def save_feedback(rdict):
    """ Save feedback file """
    # Check for output folder
    if not os.path.exists('/.__output'):
        os.makedirs('/.__output/')
    
    jcont = json.dumps(rdict)
    f = open('/.__output/__feedback.json', 'w')
    f.write(jcont)
    f.close()

# Doing the real stuff
def set_result(result):
    """ Set global result value """
    rdict = load_feedback()
    rdict['result'] = result
    save_feedback(rdict)
    
def set_global_feedback(feedback):
    """ Set global feedback in case of error """
    rdict = load_feedback()
    rdict['text'] = feedback
    save_feedback(rdict)

def set_problem_feedback(feedback, problem_id):
    """ Set problem specific feedback """
    rdict = load_feedback()
    if not 'problems' in rdict:
        rdict['problems'] = {}
    rdict['problems'][problem_id] = feedback
    save_feedback(rdict)

def get_feedback():
    """ Returns the dictionary containing the feedback """
    rdict = load_feedback()
    return rdict
