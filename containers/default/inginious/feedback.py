#!/usr/bin/python
import os
import sys
import json
import getopt

def load_feedback():
    """ Open existing feedback file """
    if os.path.exists('/.__output/__feedback.json'):
        f = open('/.__output/__feedback.json', 'r')
        cont = f.read()
        f.close()
    else:
        cont = '{}'
    return json.loads(cont)

def save_feedback(rdict):
    """ Save feedback file """
    # Check for output folder
    try:
        os.makedirs('/.__output/')
    except OSError, e:
        pass
    
    jcont = json.dumps(rdict)
    f = codecs.open('/.__output/__feedback.json', 'w')
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
