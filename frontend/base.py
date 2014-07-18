""" Basic dependencies for the frontend """
from gridfs import GridFS
from pymongo import MongoClient
import web


def add_to_template_globals(name, value):
    """ Add a variable to will be accessible in the templates """
    add_to_template_globals.globals[name] = value
add_to_template_globals.globals = {}

# Instance of the template renderer
renderer = web.template.render('templates/', globals=add_to_template_globals.globals, base='layout')


def new_database_client():
    """ Creates a new MongoClient instance for INGINious """
    return MongoClient().INGInious


def new_gridfs_client(mongo_database):
    """ Creates a new link to the GridFS of the given database """
    return GridFS(mongo_database)

database = new_database_client()
gridfs = new_gridfs_client(database)
