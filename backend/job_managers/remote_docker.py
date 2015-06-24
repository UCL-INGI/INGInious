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
""" A JobManager that can interact with distant agents, via RPyC """

from backend.job_managers.remote_manual_agent import RemoteManualAgentJobManager
import docker
import docker.utils

AGENT_CONTAINER_VERSION="0.1"

class RemoteDockerJobManager(RemoteManualAgentJobManager):
    """ A Job Manager that automatically launch Agents on distant Docker daemons """

    def __init__(self, docker_daemons, hook_manager=None, is_testing=False):
        """
            Starts the job manager.

            Arguments:

            *docker_daemons*:
                a list of dict representing docker daemons.

                { "remote_host": "192.168.59.103", ## host of the docker daemon *from the frontend*
                  "remote_docker_port": 2375, ## port of the distant docker daemon *from the frontend*
                  "remote_agent_port": 63456 ## a mandatory port used by the backend and the agent that will be automatically started. Needs to be
                                             ## available on the remote host, and to be open in the firewall.
                  ##does the docker daemon requires tls? Defaults to false
                  #use_tls: false
                  ##link to the docker daemon *from the host that runs the docker daemon*. Defaults to:
                  #"local_location": "unix:///var/run/docker.sock"
                  ##path to the cgroups "mount" *from the host that runs the docker daemon*. Defaults to:
                  #"cgroups_location": "/sys/fs/cgroup"
                }

            *hook_manager*
                An instance of HookManager. If no instance is given, a new one will be created.

        """
        agents = []

        for daemon in docker_daemons:
            docker_connection = docker.Client(base_url="tcp://"+daemon['remote_host']+":"+str(int(daemon["remote_docker_port"])), tls=daemon.get(
                "use_tls",False))

            # Verify if the container is available and at the right version
            container_already_started = False
            try:
                container_data = docker_connection.inspect_container("inginious-agent")
                if container_data["Config"]["Labels"]["agent-version"] != AGENT_CONTAINER_VERSION:
                    #kill the container
                    docker_connection.kill("inginious-agent")
                    docker_connection.remove_container("inginious-agent", force=True)
                elif container_data["State"]["Running"] is False:
                    # remove the container and restart it
                    docker_connection.remove_container("inginious-agent", force=True)
                else:
                    container_already_started = True
            except:
                pass

            if not container_already_started:
                # Verify that the image ingi/inginious-agent exists and is up-to-date
                need_download = False
                try:
                    image_data = docker_connection.inspect_image("ingi/inginious-agent")
                    if image_data["Config"]["Labels"]["agent-version"] != AGENT_CONTAINER_VERSION:
                        print "Container image ingi/inginious-agent is not up-to-date. Updating it."
                        need_download = True
                except:
                    print "Container image ingi/inginious-agent is not available on the remote docker daemon. Downloading it."
                    need_download = True

                # Download the container image...
                if need_download:
                    docker_connection.pull("ingi/inginious-agent")

                    # Verify again that the image is ok
                    try:
                        image_data = docker_connection.inspect_image("ingi/inginious-agent")
                        if image_data["Config"]["Labels"]["agent-version"] != AGENT_CONTAINER_VERSION:
                            raise Exception("Invalid version")
                    except:
                        print "The downloaded image ingi/inginious-agent is not at the same version as this instance of INGInious. Please update" \
                              " INGInious or pull manually a valid version of the container image ingi/inginious-agent."
                        exit(1)

                docker_local_location = daemon.get("local_location", "unix:///var/run/docker.sock")
                environment = {"AGENT_CONTAINER_NAME": "inginious-agent", "AGENT_PORT": daemon.get("remote_agent_port", 63456)}
                volumes = {'/sys/fs/cgroup/': {}}
                binds = {daemon.get('cgroups_location', "/sys/fs/cgroup"): {'ro': False, 'bind': "/sys/fs/cgroup"}}

                if docker_local_location.startswith("unix://"):
                    volumes['/var/run/docker.sock'] = {}
                    binds[docker_local_location[7:]] = {'ro': False, 'bind': '/var/run/docker.sock'}
                    environment["DOCKER_HOST"] = "unix:///var/run/docker.sock"
                elif docker_local_location.startswith("tcp://"):
                    environment["DOCKER_HOST"] = docker_local_location
                    if daemon.get("use_tls", False):
                        environment["DOCKER_TLS_VERIFY"] = "on"
                else:
                    raise Exception("Unknown protocol for local docker daemon: "+ docker_local_location)

                response = docker_connection.create_container(
                    "ingi/inginious-agent",
                    environment=environment,
                    detach=True,
                    name="inginious-agent",
                    volumes=volumes
                )
                container_id = response["Id"]

                # Start the container
                docker_connection.start(container_id, network_mode="host", binds=binds, restart_policy="always")

            agents.append({"host": daemon['remote_host'], "port": daemon.get("remote_agent_port", 63456)})

        RemoteManualAgentJobManager.__init__(self, agents, hook_manager, is_testing)