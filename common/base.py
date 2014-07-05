import re

#Tasks directory (created by the Makefile)
tasksDirectory = "../out/tasks/"

def IdChecker(idToTest):
    """Checks if a id is correct"""
    return bool(re.match('[a-z0-9\-_\.]+$', idToTest, re.IGNORECASE))