# -*- coding: utf8 -*-
# Author: Adrien Bibal
# Date: 2014
# Insert the student answer in the correction framework file. 

import sys
import codecs

input_file = sys.stdin # input = file containing the student answer.
oz_file = codecs.open("/task/task.oz", "r", "utf8") # Open the "correction framework file".
new_file = codecs.open("new_file.oz", "w","utf8")   # Open the final file.

for line in oz_file:
    # "@@q1@@" is the arbitrary marker used to say "insert the student answer here".
    if "@@q1@@" in line :
        for input_line in input_file :
            if '\0' in input_line :
                input_line = input_line.strip('\0')
            new_file.write(input_line) # Copy each line from the student answer to the final file.
    else :
        new_file.write(line) # Copy each line from the "correction framework file" to the final file.

oz_file.close()
new_file.close()
