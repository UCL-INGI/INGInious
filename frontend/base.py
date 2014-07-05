import web

import frontend.user as User


#Define global variables accessible from the templates
templateGlobals = {'User': User}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=templateGlobals, base='layout')
