from gridfs import GridFS
from pymongo import MongoClient
import web

from common.courses import Course
from common.tasks import Task
import frontend.user as User
import frontend.user_data


#Define global variables accessible from the templates
templateGlobals = {'User': User,'UserData':frontend.user_data.UserData,'Task': Task,'Course': Course}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=templateGlobals, base='layout')

def newDatabaseClient():
    return MongoClient().INGInious
def newGridFSClient(database):
    return GridFS(database)

database = newDatabaseClient()
gridFS = newGridFSClient(database)