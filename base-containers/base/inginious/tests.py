#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import sys
import json

import inginious

_tests_dir = '/.__tests' if not inginious.DEBUG else './'
_tests_file = os.path.join(_tests_dir, '__tests.json')

def load_tests():
    """ Open existing tests file """
    result = {}
    if os.path.exists(_tests_file):
        f = open(_tests_file, 'r')
        cont = f.read()
        f.close()
    else:
        cont = '{}'
    try:
        result = json.loads(cont)
    except ValueError as e:
        result = {"result":"crash", "text":"Tests file has been modified by user !"}
    return result

def save_tests(rdict):
    """ Save tests file """
    # Check for output folder
    if not os.path.exists(_tests_dir):
        os.makedirs(_tests_dir)
    
    jcont = json.dumps(rdict)
    f = open(_tests_file, 'w')
    f.write(jcont)
    f.close()

# Doing the real stuff
def set_result(tag, value):
    """ Set result value value """
    rdict = load_tests()
    rdict[tag] = value
    save_tests(rdict)

def get_tests_results():
    """ Returns the dictionary containing the feedback """
    rdict = load_tests()
    return rdict
