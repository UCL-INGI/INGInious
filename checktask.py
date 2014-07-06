"""
    Small tool to allow verification of .task and .course files.
    Usage:
        python checktask.py file.task
        python checktask.py file.course
"""
import os
import sys

import common.base


def usage():
    print "Usage: "
    print "\tpython checktask.py file.task"
    print "\tpython checktask.py file.course"
    exit(1)

if len(sys.argv) != 2:
    usage()

# Change default path to task Directory
common.base.tasksDirectory = os.path.dirname(sys.argv[1])
# Get composants of the filename
filename = os.path.splitext(os.path.basename(sys.argv[1]))

from common.courses import Course #Must be done after changements on tasksDirectory
from common.tasks import Task

if filename[1] not in [".task", ".course"]:
    print "This tool only support file with extension .task or .course"
    usage()

try:
    if filename[1] == ".task":
        Task("", filename[0])
    else:
        Course(filename[0])
except Exception as inst:
    print "There was an error while validating the file:"
    print inst
else:
    print "File verification succeeded"
