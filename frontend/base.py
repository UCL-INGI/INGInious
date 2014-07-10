import web

import frontend.user as User
from common.tasks import Task
from common.courses import Course
from pymongo import MongoClient
from gridfs import GridFS

#Define global variables accessible from the templates
templateGlobals = {'User': User,'Task': Task,'Course': Course}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=templateGlobals, base='layout')

def newDatabaseClient():
    return MongoClient().INGInious
def newGridFSClient(database):
    return GridFS(database)

database = newDatabaseClient()
gridFS = newGridFSClient(database)