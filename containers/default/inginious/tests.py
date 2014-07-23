#!/usr/bin/python
import os
import sys
import json

def load_tests():
    """ Open existing tests file """
    result = {}
    if os.path.exists('/.__tests/__tests.json'):
        f = open('/.__tests/__tests.json', 'r')
        cont = f.read()
        f.close()
    else:
        cont = '{}'
    try:
        result = json.loads(cont)
    except ValueError, e:
        result = {"result":"crash", "text":"Tests file has been modified by user !"}
    return result

def save_tests(rdict):
    """ Save tests file """
    # Check for output folder
    if not os.path.exists('/.__tests'):
        os.makedirs('/.__tests/')
    
    jcont = json.dumps(rdict)
    f = open('/.__tests/__tests.json', 'w')
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
