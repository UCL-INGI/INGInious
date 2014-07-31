# -*- coding: utf8 -*-
# Author: Adrien Bibal
# Date: 2014
# This file contains methods that add a tip in runtime error messages.

# msg is the error message given by the compiler.
# checkMissingElseClause checks if the error message is a "missing else clause" message.
# If this is the case, add a message with the problematic line number.
def checkMissingElseClause(msg):
    error_message = ""
    if "Missing else clause" in msg: # Check if we deal with the "missing else clause" message.
        msg = msg.split("Missing else clause") # msg is now an array.
        error_message = "At line(s):"
        lines = ""
        for i in range(1, len(msg)): # For each "Missing else clause"
            if "in file \"Oz\", line " in msg[i]: # If we are the line containing the problematic line number.
                lines += " " + msg[i].split("in file \"Oz\", line ")[1].split("\n%**")[0] + ","
        error_message += lines + " it seems you have forgotten a condition in your if/elseif/else clauses.\n"
    return error_message

# msg is the error message given by the compiler.
# checkIllegalFieldSelection checks if the error message is an "illegal field selection" message.
# If this is the case, add a tip with the problematic line number.
def checkIllegalFieldSelection(msg):
    error_message = ""
    if "Error: illegal field selection" in msg: # Check if we deal with the "illegal field selection" message.
        # Adding the tip.
        error_message = "It seems that you tried to select a field that does not exist. This may arrive, for instance, if you try to access to the head (with .1) or the queue (with .2) of a list L, while L is nil. Therefore, as nil does not have any field name 1 or 2, nil.1 and nil.2 raise an error.\n"
    return error_message

def checkMaximalHeapSize(msg):
    error_message = ""
    if "GC is over the maximal heap size threshold" in msg: # Check if we deal with the "maximal heap size" message.
        # Adding the tip.
        error_message = "It seems a part of your code generate a large amount of memory allocation. This may happen if one of your recursive functions does not terminate.\n\n"
    return error_message

def checkCPUTimeLimit(msg):
    error_message = ""
    if "CPU time limit exceeded" in msg: # Check if we deal with the "CPU time limit exceeded" message.
        # Adding the tip.
        error_message = "It seems one of your loops (or recursive) functions does not terminate, or a big delay increases the time needed by your code to execute. In all cases, your code took too much time to run. \n\n"
    return error_message
