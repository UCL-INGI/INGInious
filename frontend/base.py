import web

import frontend.user as User
from pymongo import MongoClient
from gridfs import GridFS

#Define global variables accessible from the templates
templateGlobals = {'User': User}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=templateGlobals, base='layout')

def newDatabaseClient():
    return MongoClient().pythia
def newGridFSClient(database):
    return GridFS(database)

database = newDatabaseClient()
gridFS = newGridFSClient(database)