# Tool to export feedback
# 

import os
import re
import sys
import codecs
import json
import getopt

# Open existing feedback file
if os.path.exists('/tmp/__feedback.json'):
    f = codecs.open('/tmp/__feedback.json', 'r', 'utf-8')
    cont = f.read()
else:
    cont = '{}'
rdict = json.loads(cont)

# Read arguments from the command line
try:
    opts, args = getopt.getopt(sys.argv[1:], 'r:f:i:p', ['result=', 'feedback=', 'id=' , 'print'])
except getopt.GetoptError,e:
    print e
    sys.exit(2)

result = ''
feedback = ''
problem = ''
getjson = False

for opt, arg in opts:
    if opt in ('-r', '--result'):
        result = arg
    elif opt in ('-f', '--feedback'):
        feedback = arg
    elif opt in ('-i', '--id'):
        problem = arg
    elif opt in ('-p', '--print'):
        getjson = True

# Doing the real stuff

if result != '':
    rdict['result'] = result
    
if feedback != '':
    if problem == '':
        rdict['text'] = feedback
    else:
        if not 'problems' in rdict:
            rdict['problems'] = {}
        rdict['problems'][problem] = feedback

jcont = json.dumps(rdict)

if getjson:
    print jcont
    
codecs.open('/tmp/__feedback.json', 'w', 'utf-8').write(jcont.strip())
