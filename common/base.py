import web
import frontend.login as Login
import re

#Define global variables accessible from the templates
templateGlobals = {'Login': Login}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=templateGlobals, base='layout')

#Tasks directory (created by the Makefile)
tasksDirectory = "../out/tasks/"

def IdChecker(idToTest):
    """Checks if a id is correct"""
    return bool(re.match('[a-z0-9\-_\.]+$', idToTest, re.IGNORECASE))