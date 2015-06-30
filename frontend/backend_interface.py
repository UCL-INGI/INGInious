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
""" Interface with the backend """

from backend.job_managers.local import LocalJobManager
from backend.job_managers.remote_docker import RemoteDockerJobManager
from backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
from frontend.base import get_database
from frontend.configuration import INGIniousConfiguration

def get_job_manager():
    """ Get the JobManager. Should only be used by very specific plugins """
    return get_job_manager.job_manager
get_job_manager.job_manager = None

def init(plugin_manager):
    """ inits everything that makes the backend working """

    # Updates the submissions that are waiting with the status error, as the server restarted
    get_database().submissions.update({'status': 'waiting'},
                                      {"$unset": {'jobid': ""},
                                       "$set": {'status': 'error', 'grade': 0.0, 'text': 'Internal error. Server restarted'}}, multi=True)

    # Updates all batch job still running
    get_database().batch_jobs.update({'result':{'$exists':False}},
                                     {"$set": {"result": {"retval": -1, "stderr": "Internal error. Server restarted"}}}, multi=True)

    # Create the job manager
    backend_type = INGIniousConfiguration.get("backend", "local")
    if backend_type == "local":
        get_job_manager.job_manager = LocalJobManager(
            INGIniousConfiguration.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
            INGIniousConfiguration.get('local_agent_tmp_dir', "/tmp/inginious_agent"), plugin_manager)
    elif backend_type == "remote":
        get_job_manager.job_manager = RemoteDockerJobManager(INGIniousConfiguration.get("docker_daemons", []),
                                                             INGIniousConfiguration.get('containers', {"default": "ingi/inginious-c-default",
                                                                                                       "sekexe": "ingi/inginious-c-sekexe"}),
                                                             plugin_manager)
    elif backend_type == "remote_manual":
        get_job_manager.job_manager = RemoteManualAgentJobManager(
            INGIniousConfiguration.get("agents", [{"host": "localhost", "port": 5001}]),
            INGIniousConfiguration.get('containers', {"default": "ingi/inginious-c-default", "sekexe": "ingi/inginious-c-sekexe"}),
            plugin_manager)
    else:
        raise Exception("Unknown backend {}".format(backend_type))


def start():
    """ Starts the backend interface. Should be called after the initialisation of the plugin manager. """
    get_job_manager().start()