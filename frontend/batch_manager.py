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
""" Manages batch containers """

import frontend.user as User
from frontend.backend_interface import get_job_manager
from frontend.configuration import INGIniousConfiguration
from frontend.base import get_database, get_gridfs

def add_batch_job(course, container_name, inputdata, launcher_name=None, skip_permission=False):
    """ Add a job in the queue and returns a batch job id """

    if not skip_permission:
        if not User.is_logged_in():
            raise Exception("A user must be logged in to submit an object")

        username = User.get_username()
        launcher_name = launcher_name or username

        if username not in course.get_admins():
            raise Exception("The user must be an administrator to start a batch job")

    if container_name not in INGIniousConfiguration.get("batch_containers", []):
        raise Exception("This batch container is not allowed to be started")

    container_args = get_job_manager().get_batch_container_args(container_name)
    if container_args is None:
        raise Exception("This batch container is not available")


    obj = {"courseid": course.get_id(), 'container_name': container_name}

    batch_job_id = get_database().batch_jobs.insert(obj)

    launcher_name = launcher_name or "plugin"

    get_job_manager().new_batch_job(container_name, inputdata, lambda r: batch_job_done_callback(batch_job_id, r),
                                    launcher_name="Frontend - {}".format(launcher_name))

    return batch_job_id

def batch_job_done_callback(batch_job_id, result):
    """ Called when the batch job with id jobid has finished. result is a file-like object pointing to a tar.gz file """
    pass