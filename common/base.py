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
""" Basic dependencies for every modules that uses INGInious """
import re

# Configuration for common modules


def get_tasks_directory():
    """ Return the path to the directory containing the courses and the tasks """
    return get_tasks_directory.tasks_directory
get_tasks_directory.tasks_directory = "trolol"


def get_allowed_file_extensions():
    """ Returns a list containing the allowed file extensions (for file uploads) """
    return get_allowed_file_extensions.allowed_file_extensions
get_allowed_file_extensions.allowed_file_extensions = [".c", ".cpp", ".java", ".oz", ".zip", ".tar.gz", ".tar.bz2", ".txt"]


def get_max_file_size():
    """ Return the maximum file upload size """
    return get_max_file_size.max_file_size
get_max_file_size.max_file_size = 1024 * 1024


def init_common_lib(tasks_directory, allowed_file_extensions, max_file_size):
    """Inits the modules in the common package"""
    get_tasks_directory.tasks_directory = tasks_directory
    get_allowed_file_extensions.allowed_file_extensions = allowed_file_extensions
    get_max_file_size.max_file_size = max_file_size


def id_checker(id_to_test):
    """Checks if a id is correct"""
    return bool(re.match(r'[a-z0-9\-_]+$', id_to_test, re.IGNORECASE))
