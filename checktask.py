"""
    Small tool to allow verification of .task and .course files.
    Usage:
        python checktask.py file.task
        python checktask.py file.course
"""
import sys

from frontend.custom.courses import FrontendCourse
from frontend.custom.tasks import FrontendTask
import common.base


def usage():
    """ Usage """
    print "Usage: "
    print "\tpython checktask.py task_directory courseid taskid"
    print "\tpython checktask.py task_directory courseid"
    exit(1)

if len(sys.argv) not in [3, 4]:
    usage()

# Change default path to task Directory
common.base.INGIniousConfiguration["allow_html"] = "tidy"
common.base.INGIniousConfiguration["tasks_directory"] = sys.argv[1]

try:
    if len(sys.argv) == 2:
        FrontendCourse(sys.argv[2])
    else:
        FrontendTask(FrontendCourse(sys.argv[2]), sys.argv[3])
except Exception as inst:
    print "There was an error while validating the file:"
    print inst
    exit(1)
else:
    print "File verification succeeded"
    exit(0)
