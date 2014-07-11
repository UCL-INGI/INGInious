# -*- coding: utf-8 -*-
# Tool to import answer from standard input to the template files given in arguments
#

import os
import re
import sys
import codecs
import json

os.mkdir("/tmp/output")

# Retrieves the input data from Pythia
input_data = json.loads(sys.stdin.read().strip('\0').strip())["input"]

for filepath in sys.argv[1:]:
    filepath = filepath
    with codecs.open(filepath, 'r', 'utf-8') as file2:
        content = file2.read()
    for field in input_data:
        regex = re.compile("@([^@]*)@" + field + '@([^@]*)@')
        for prefix, postfix in set(regex.findall(content)):
            rep = "\n".join([prefix + v + postfix for v in input_data[field].splitlines()])
            content = content.replace("@{0}@{1}@{2}@".format(prefix, field, postfix), rep)
    with codecs.open(filepath, 'w', 'utf-8') as file3:
        file3.write(content)
