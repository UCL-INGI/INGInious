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
""" Interface with the inginious.backend """

from inginious.backend.job_managers.local import LocalJobManager
from inginious.backend.job_managers.remote_docker import RemoteDockerJobManager
from inginious.backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager


def update_pending_jobs(database):
    """ Updates pending jobs status in the database """

    # Updates the submissions that are waiting with the status error, as the server restarted
    database.submissions.update({'status': 'waiting'},
                                {"$unset": {'jobid': ""},
                                 "$set": {'status': 'error', 'grade': 0.0, 'text': 'Internal error. Server restarted'}}, multi=True)

    # Updates all batch job still running
    database.batch_jobs.update({'result': {'$exists': False}},
                               {"$set": {"result": {"retval": -1, "stderr": "Internal error. Server restarted"}}}, multi=True)


def create_job_manager(configuration, plugin_manager, task_directory, course_factory, task_factory, is_testing=False):
    """ Creates a new inginious.backend job manager from the configuration """

    # Create the job manager
    backend_type = configuration.get("backend", "local")
    if backend_type == "local":
        return LocalJobManager(configuration.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
                               task_directory,
                               course_factory,
                               task_factory,
                               configuration.get('local_agent_tmp_dir', "/tmp/inginious_agent"), plugin_manager, is_testing)
    elif backend_type == "remote":
        return RemoteDockerJobManager(configuration.get("docker_daemons", []),
                                      configuration.get('containers',
                                                        {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
                                      task_directory,
                                      course_factory,
                                      task_factory,
                                      plugin_manager, is_testing)
    elif backend_type == "remote_manual":
        return RemoteManualAgentJobManager(
            configuration.get("agents", [{"host": "localhost", "port": 5001}]),
            configuration.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
            task_directory,
            course_factory,
            task_factory,
            plugin_manager, is_testing)
    else:
        raise Exception("Unknown inginious.backend {}".format(backend_type))
