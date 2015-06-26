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
import codecs
import json
import os.path
import hashlib
import re
import common.custom_yaml

# Configuration for common modules


def get_tasks_directory():
    """ Return the path to the directory containing the courses and the tasks """
    return get_tasks_directory.tasks_directory
get_tasks_directory.tasks_directory = "./tasks"


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
    get_max_file_size.max_file_size = int(max_file_size) if max_file_size is not None else (1024 * 1024)


def id_checker(id_to_test):
    """Checks if a id is correct"""
    return bool(re.match(r'[a-z0-9\-_]+$', id_to_test, re.IGNORECASE))


def load_json_or_yaml(file_path):
    """ Load JSON or YAML depending on the file extension. Returns a dict """
    if os.path.splitext(file_path)[1] == ".json":
        return json.load(open(file_path, "r"))
    else:
        return common.custom_yaml.load(open(file_path, "r"))


def write_json_or_yaml(file_path, content):
    """ Load JSON or YAML depending on the file extension. """
    if os.path.splitext(file_path)[1] == ".json":
        o = json.dumps(content, sort_keys=False, indent=4, separators=(',', ': '))
    else:
        o = common.custom_yaml.dump(content)

    with codecs.open(file_path, "w", "utf-8") as f:
        f.write(o)

def hash_file(fileobj):
    """
    :param fileobj: a file object
    :return: a hash of the file content
    """
    hasher = hashlib.md5()
    buf = fileobj.read(65536)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fileobj.read(65536)
    return hasher.hexdigest()

def directory_content_with_hash(directory):
    """
    :param directory: directory in which the function list the files
    :return: dict in the form {file: (hash of the file, stat of the file)}
    """
    output = {}
    for root, directories, filenames in os.walk(directory):
        for filename in filenames:
            p = os.path.join(root, filename)
            file_stat = os.stat(p)
            with open(p, 'rb') as f:
                output[os.path.relpath(p, directory)] = (hash_file(f), file_stat.st_mode)
    return output

def directory_compare_from_hash(from_directory, to_directory):
    """
    :param from_directory: dict in the form {file: (hash of the file, stat of the file)} from directory_content_with_hash
    :param to_directory: dict in the form {file: (hash of the file, stat of the file)} from directory_content_with_hash
    :return: a tuple containing two list: the files that should be uploaded to "to_directory" and the files that should be removed from "to_directory"
    """
    to_upload = []
    to_delete = []
    for path, (hash, stat) in from_directory.iteritems():
        if not path in to_directory or to_directory[path] != (hash, stat):
            to_upload.append(path)
    for path in to_directory:
        if path not in from_directory:
            to_delete.append(path)
    return (to_upload, to_delete)