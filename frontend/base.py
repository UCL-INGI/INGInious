""" Basic dependencies for the frontend """
from gridfs import GridFS
from pymongo import MongoClient
import web

from common.courses import Course
from common.tasks import Task
import frontend.user as User
import frontend.user_data


# Define global variables accessible from the templates
_template_globals = {'User': User, 'UserData': frontend.user_data.UserData, 'Task': Task, 'Course': Course}
# Instance of the template renderer
renderer = web.template.render('templates/', globals=_template_globals, base='layout')


def new_database_client():
    """ Creates a new MongoClient instance for INGINious """
    return MongoClient().INGInious


def new_gridfs_client(mongo_database):
    """ Creates a new link to the GridFS of the given database """
    return GridFS(mongo_database)

database = new_database_client()
gridfs = new_gridfs_client(database)