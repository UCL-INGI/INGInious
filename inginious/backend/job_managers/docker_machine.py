# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A Job Manager that automatically launch Agents on Docker Machines """
import logging
import subprocess
import sys

import json

from inginious.backend.job_managers.remote_docker import RemoteDockerJobManager

AGENT_CONTAINER_VERSION = "0.5"


class DockerMachineJobManager(RemoteDockerJobManager):
    """ A Job Manager that automatically launch Agents on Docker Machines """

    @classmethod
    def get_machine(cls, machine):
        logger = logging.getLogger("inginious.backend")

        base_dict = {
            "remote_agent_port":63456,
            "remote_docker_port": 2376,  # todo: is it possible with Docker-machine to have a different port?
            "remote_agent_ssh_port": 63457
        }
        if isinstance(machine, dict):
            base_dict.update(machine)
            del base_dict["name"]
            machine = machine["name"]

        p = subprocess.Popen(["docker-machine", "start", machine], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        p = subprocess.Popen(["docker-machine", "inspect", machine], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.wait() != 0:
            logger.error("An error occured while running the docker-machine inspect command on {}".format(machine))
            logger.error("INGInious will now exit. Here is the output of docker-machine inspect:")
            logger.error(p.stdout.read().decode('utf-8'))
            logger.error(p.stderr.read().decode('utf-8'))
            exit(1)
        data = json.loads(p.stdout.read().decode('utf-8'))

        use_tls = {
            "cert": data["HostOptions"]["AuthOptions"]["ServerCertPath"],
            "key":  data["HostOptions"]["AuthOptions"]["ServerKeyPath"],
            "ca":   data["HostOptions"]["AuthOptions"]["CaCertPath"]
        }

        base_dict["remote_host"] = data["Driver"]["IPAddress"]
        base_dict["use_tls"] = use_tls

        #FIXME we temporarilly disable usage of TLS while using Docker-machine as requests has a problem with the SSL verification of the certificates
        #      see https://github.com/docker/docker-py/issues/706 (among others)
        import requests.packages.urllib3
        requests.packages.urllib3.disable_warnings()
        base_dict["use_tls"]["ca"] = False
        return base_dict


    def __init__(self, machines, image_aliases, task_directory, course_factory, task_factory, hook_manager=None, is_testing=False):
        """
            Starts the job manager.

            :param machines:
                a list of strings that names machines available in docker-machine.

                Alternatively, the strings can be replaced by a dict; If it is the case, it should contains at least a key named "name",
                which contains the name of the machine in docker-machine. Other keys/values will be passed to the underlying RemoteDockerJobManager.
            :param task_directory: the task directory
            :param course_factory: a CourseFactory object
            :param task_factory: a TaskFactory object, possibly with specific task files managers attached
            :param image_aliases: a dict of image aliases, like {"default": "ingi/inginious-c-default"}.
            :param hook_manager: An instance of HookManager. If no instance is given(None), a new one will be created.
        """
        docker_daemons = list(map(self.get_machine, machines))
        super(DockerMachineJobManager, self).__init__(docker_daemons, image_aliases, task_directory, course_factory, task_factory, hook_manager,
                                                      is_testing)