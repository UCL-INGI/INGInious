# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    (not asyncio) Interface to Docker
"""
import json
import os
import re

import docker


class DockerInterface(object):
    """
        (not asyncio) Interface to Docker
    """

    def __init__(self):
        self._docker = docker.Client()

    def get_containers(self):
        """
        :return: a dict of available containers in the form
        {
            "name": {                          #for example, "default"
                "id": "container img id",      #             "sha256:715c5cb5575cdb2641956e42af4a53e69edf763ce701006b2c6e0f4f39b68dd3"
                "created": 12345678            # create date
            }
        }
        """

        # First, create a dict with {"id": {"title": "alias", "created": 000}}
        images = {x['Id']: {"title": x['Labels']["org.inginious.grading.name"], "created": int(x['Created'])}
                  for x in self._docker.images(filters={"label": "org.inginious.grading.name"})}

        # Then, we keep only the last version of each name
        latest = {}
        for img_id, img_c in images.items():
            if img_c["title"] not in latest or latest[img_c["title"]]["created"] < img_c["created"]:
                latest[img_c["title"]] = {"id": img_id, "created": img_c["created"]}
        return latest

    def get_batch_containers(self):
        """
        :return: {
                    "name": {
                        "description": "a description written in RST",
                        "id": "container img id",
                        "created": 123456789
                        "parameters": {
                            "key": {
                                 "type:" "file", #or "text",
                                 "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                                 "name": "name of the field", #not mandatory in file, default "key"
                                 "description": "a short description of what this field is used for" #not mandatory, default ""
                            }
                        }
                }
        """
        images = {x['Id']: {"title": x['Labels']["org.inginious.batch.name"], "created": int(x['Created']), "labels": x['Labels']}
                  for x in self._docker.images(filters={"label": "org.inginious.batch.name"})}

        # Then, we keep only the last version of each name
        latest = {}
        for img_id, img_c in images.items():
            if img_c["title"] not in latest or latest[img_c["title"]]["created"] < img_c["created"]:
                latest[img_c["title"]] = {"id": img_id, "created": img_c["created"], "labels": img_c["labels"]}

        # Now, we parse the labels
        parsed = {}
        for img_title, img_content in latest.items():
            data = img_content["labels"]
            description = data["org.inginious.batch.description"] if "org.inginious.batch.description" in data else ""

            # Find valids keys
            args = {}
            for label in data:
                match = re.match(r"^org\.inginious\.batch\.args\.([a-zA-Z0-9\-_]+)$", label)
                if match and data[label] in ["file", "text"]:
                    args[match.group(1)] = {"type": data[label]}

            # Parse additional metadata for the keys
            for label in data:
                match = re.match(r"^org\.inginious\.batch\.args\.([a-zA-Z0-9\-_]+)\.([a-zA-Z0-9\-_]+)$", label)
                if match and match.group(1) in args:
                    if match.group(2) in ["name", "description"]:
                        args[match.group(1)][match.group(2)] = data[label]
                    elif match.group(2) == "path":
                        if re.match(r"^[a-zA-Z\-_\./]+$", data[label]) and ".." not in data[label]:
                            args[match.group(1)]["path"] = data[label]
                    else:
                        args[match.group(1)][match.group(2)] = data[label]

            # Add all the unknown metadata
            for key in args:
                if "name" not in args[key]:
                    args[key]["name"] = key
                if "path" not in args[key]:
                    args[key]["path"] = key
                if "description" not in args[key]:
                    args[key]["description"] = ""

            parsed[img_title] = {
                "created": img_content["created"],
                "id": img_content["id"],
                "description": description,
                "parameters": args
            }

        return parsed

    def create_container(self, environment, debug, network_grading, mem_limit, task_path, sockets_path):
        """
        Creates a container.
        :param environment: env to start (name/id of a docker image)
        :param debug: True/False or "ssh"
        :param network_grading: boolean to indicate if the network should be enabled in the container or not
        :param mem_limit: in Mo
        :param task_path: path to the task directory that will be mounted in the container
        :param sockets_path: path to the socket directory that will be mounted in the container
        """
        task_path = os.path.abspath(task_path)
        sockets_path = os.path.abspath(sockets_path)

        response = self._docker.create_container(
            environment,
            stdin_open=True,
            volumes=['/task', '/sockets'],
            # network_disabled=not (network_grading or debug == "ssh"), #set in host_config, makes docker do strange things instead
            host_config=self._docker.create_host_config(
                mem_limit=str(mem_limit) + "M",
                memswap_limit=str(mem_limit) + "M",
                mem_swappiness=0,
                oom_kill_disable=True,
                network_mode=("bridge" if (network_grading or debug == "ssh") else 'none'),
                binds={task_path: {'bind': '/task'},
                       sockets_path: {'bind': '/sockets'}}
            )
        )
        return response["Id"]

    def create_container_student(self, parent_container_id, environment, network_grading, mem_limit, student_path, socket_path, systemfiles_path):
        """
        Creates a student container
        :param parent_container_id: id of the "parent" container
        :param environment: env to start (name/id of a docker image)
        :param network_grading: boolean to indicate if the network should be enabled in the container or not (share the parent stack)
        :param mem_limit: in Mo
        :param student_path: path to the task directory that will be mounted in the container
        :param socket_path: path to the socket that will be mounted in the container
        :param systemfiles_path: path to the systemfiles folder containing files that can override partially some defined system files
        """
        student_path = os.path.abspath(student_path)
        socket_path = os.path.abspath(socket_path)
        systemfiles_path = os.path.abspath(systemfiles_path)

        response = self._docker.create_container(
            environment,
            stdin_open=True,
            volumes=['/task/student', '/__parent.sock', '/task/systemfiles'],
            command="_run_student_intern",
            host_config=self._docker.create_host_config(
                mem_limit=str(mem_limit) + "M",
                memswap_limit=str(mem_limit) + "M",
                mem_swappiness=0,
                oom_kill_disable=True,
                network_mode=('none' if not network_grading else ('container:' + parent_container_id)),
                binds={student_path: {'bind': '/task/student'},
                       socket_path: {'bind': '/__parent.sock'},
                       systemfiles_path: {'bind': '/task/systemfiles', 'mode': 'ro'}}
            )
        )
        return response["Id"]

    def start_container(self, container_id):
        """ Starts a container (obviously) """
        self._docker.start(container_id)

    def attach_to_container(self, container_id):
        """ A socket attached to the stdin/stdout of a container """
        return self._docker.attach_socket(container_id, {
            'stdin': 1,
            'stdout': 1,
            'stderr': 0,
            'stream': 1,
        })

    def get_logs(self, container_id):
        """ Return the full stdout of a container (parsed with json) """
        stdout = self._docker.logs(container_id, stdout=True, stderr=False).decode('utf8')
        stderr = self._docker.logs(container_id, stdout=False, stderr=True).decode('utf8')
        # TODO SSH
        # if debug == "ssh":  # skip the first line of the output, that contained the ssh key
        #     stdout = "\n".join(stdout.split("\n")[1:])
        return json.loads(stdout)

    def get_stats(self, container_id):
        """
        :param container_id:
        :return: an iterable that contains dictionnaries with the stats of the running container. See the docker api for content.
        """
        return self._docker.stats(container_id, decode=True)

    def remove_container(self, container_id):
        """
        Removes a container (with fire)
        """
        self._docker.remove_container(container_id, True, False, True)

    def kill_container(self, container_id, signal=None):
        """
        Kills a container
        :param signal: custom signal. Default is SIGKILL.
        """
        self._docker.kill(container_id, signal)

    def event_stream(self, filters={}):
        """
        :param filters: filters to apply on messages. See docker api.
        :return: an iterable that contains events from docker. See the docker api for content.
        """
        return self._docker.events(decode=True, filters=filters)
