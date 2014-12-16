# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Basic dependencies for the frontend """
from gridfs import GridFS
from pymongo import MongoClient
import web
from common.base import INGIniousConfiguration


def add_to_template_globals(name, value):
    """ Add a variable to will be accessible in the templates """
    add_to_template_globals.globals[name] = value
add_to_template_globals.globals = {}


def get_template_renderer(dir_path, base=None):
    """ Create a template renderer on templates in the directory specified.
        *base* is the base layout name.
    """
    return web.template.render(dir_path, globals=add_to_template_globals.globals, base=base)

renderer = get_template_renderer('templates/', 'layout')


def new_database_client():
    """ Creates a new MongoClient instance for INGINious """
    config = {'host': INGIniousConfiguration.get('mongo_opt', {}).get('host', 'localhost')}
    client = MongoClient(**config)
    return client[INGIniousConfiguration.get('mongo_opt', {}).get('database', 'INGInious')]


def new_gridfs_client(mongo_database):
    """ Creates a new link to the GridFS of the given database """
    return GridFS(mongo_database)


def get_database():
    """ Returns an access to the database """
    return get_database.database


def get_gridfs():
    """ Returns an access to gridfs """
    return get_gridfs.gridfs


def init_database():
    """ Init the db clients"""
    get_database.database = new_database_client()
    get_gridfs.gridfs = new_gridfs_client(get_database())
