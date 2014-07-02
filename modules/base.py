import web
from modules.login import loginInstance

#Define global variables accessible from the templates
templateGlobals = {'loginInstance': loginInstance}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=templateGlobals, base='layout')

#Tasks directory (created by the Makefile)
tasksDirectory = "../out/tasks/"
