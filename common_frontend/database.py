# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
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
""" Manages the database """
from gridfs import GridFS
from pymongo import MongoClient

from common_frontend.configuration import INGIniousConfiguration


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