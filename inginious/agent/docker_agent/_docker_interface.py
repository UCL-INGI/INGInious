# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

"""
    (not asyncio) Interface to Docker
"""
import os
from datetime import datetime
import docker

class DockerInterface(object):  # pragma: no cover
    """
        (not asyncio) Interface to Docker

        We do not test coverage here, as it is a bit complicated to interact with docker in tests.
        Docker-py itself is already well tested.
    """

    @property
    def _docker(self):
        return docker.from_env()
    
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
        images = {x.attrs['Id']: {"title": x.labels["org.inginious.grading.name"], "created": datetime.strptime(x.attrs['Created'][:-4], "%Y-%m-%dT%H:%M:%S.%f").timestamp()}
                  for x in self._docker.images.list(filters={"label": "org.inginious.grading.name"})}

        # Then, we keep only the last version of each name
        latest = {}
        for img_id, img_c in images.items():
            if img_c["title"] not in latest or latest[img_c["title"]]["created"] < img_c["created"]:
                latest[img_c["title"]] = {"id": img_id, "created": img_c["created"]}
        return latest

    def get_host_ip(self, env_with_dig='ingi/inginious-c-default'):
        """
        Get the external IP of the host of the docker daemon. Uses OpenDNS internally.
        :param env_with_dig: any container image that has dig
        """
        try:
            container = self._docker.containers.create(env_with_dig, command="dig +short myip.opendns.com @resolver1.opendns.com")
            container.start()
            response = container.wait()
            assert response["StatusCode"] == 0 if isinstance(response, dict) else response == 0
            answer = container.logs(stdout=True, stderr=False).decode('utf8').strip()
            container.remove(v=True, link=False, force=True)
            return answer
        except:
            return None

    def create_container(self, environment, network_grading, mem_limit, task_path, sockets_path,
                         course_common_path, course_common_student_path, ssh_port=None):
        """
        Creates a container.
        :param environment: env to start (name/id of a docker image)
        :param debug: True/False or "ssh"
        :param network_grading: boolean to indicate if the network should be enabled in the container or not
        :param mem_limit: in Mo
        :param task_path: path to the task directory that will be mounted in the container
        :param sockets_path: path to the socket directory that will be mounted in the container
        :param ssh_port: port that will be bound to 22 inside the container
        :return: the container id
        """
        task_path = os.path.abspath(task_path)
        sockets_path = os.path.abspath(sockets_path)
        course_common_path = os.path.abspath(course_common_path)
        course_common_student_path = os.path.abspath(course_common_student_path)

        response = self._docker.containers.create(
            environment,
            stdin_open=True,
            mem_limit=str(mem_limit) + "M",
            memswap_limit=str(mem_limit) + "M",
            mem_swappiness=0,
            oom_kill_disable=True,
            network_mode=("bridge" if (network_grading or ssh_port is not None) else 'none'),
            ports= {22: ssh_port} if ssh_port is not None else {},
            volumes={
                task_path: {'bind': '/task'},
                sockets_path: {'bind': '/sockets'},
                course_common_path: {'bind': '/course/common', 'mode': 'ro'},
                course_common_student_path: {'bind': '/course/common/student', 'mode': 'ro'}
            }
        )
        return response.id

    def create_container_student(self, parent_container_id, environment, network_grading, mem_limit,  student_path,
                                 socket_path, systemfiles_path, course_common_student_path):
        """
        Creates a student container
        :param parent_container_id: id of the "parent" container
        :param environment: env to start (name/id of a docker image)
        :param network_grading: boolean to indicate if the network should be enabled in the container or not (share the parent stack)
        :param mem_limit: in Mo
        :param student_path: path to the task directory that will be mounted in the container
        :param socket_path: path to the socket that will be mounted in the container
        :param systemfiles_path: path to the systemfiles folder containing files that can override partially some defined system files
        :return: the container id
        """
        student_path = os.path.abspath(student_path)
        socket_path = os.path.abspath(socket_path)
        systemfiles_path = os.path.abspath(systemfiles_path)
        course_common_student_path = os.path.abspath(course_common_student_path)

        response = self._docker.containers.create(
            environment,
            stdin_open=True,
            command="_run_student_intern",
            mem_limit=str(mem_limit) + "M",
            memswap_limit=str(mem_limit) + "M",
            mem_swappiness=0,
            oom_kill_disable=True,
            network_mode=('none' if not network_grading else ('container:' + parent_container_id)),
            volumes={
                student_path: {'bind': '/task/student'},
                 socket_path: {'bind': '/__parent.sock'},
                 systemfiles_path: {'bind': '/task/systemfiles', 'mode': 'ro'},
                 course_common_student_path: {'bind': '/course/common/student', 'mode': 'ro'}
            }
        )
        return response.id

    def start_container(self, container_id):
        """ Starts a container (obviously) """
        self._docker.containers.get(container_id).start()

    def attach_to_container(self, container_id):
        """ A socket attached to the stdin/stdout of a container. The object returned contains a get_socket() function to get a socket.socket
        object and  close_socket() to close the connection """
        sock = self._docker.containers.get(container_id).attach_socket(params={
            'stdin': 1,
            'stdout': 1,
            'stderr': 0,
            'stream': 1,
        })
        # fix a problem with docker-py; we must keep a reference of sock at every time
        return FixDockerSocket(sock)

    def get_logs(self, container_id):
        """ Return the full stdout/stderr of a container"""
        stdout = self._docker.containers.get(container_id).logs(stdout=True, stderr=False).decode('utf8')
        stderr = self._docker.containers.get(container_id).logs(stdout=False, stderr=True).decode('utf8')
        return stdout, stderr

    def get_stats(self, container_id):
        """
        :param container_id:
        :return: an iterable that contains dictionnaries with the stats of the running container. See the docker api for content.
        """
        return self._docker.containers.get(container_id).stats(decode=True)

    def remove_container(self, container_id):
        """
        Removes a container (with fire)
        """
        self._docker.containers.get(container_id).remove(v=True, link=False, force=True)

    def kill_container(self, container_id, signal=None):
        """
        Kills a container
        :param signal: custom signal. Default is SIGKILL.
        """
        self._docker.containers.get(container_id).kill(signal)

    def event_stream(self, filters=None):
        """
        :param filters: filters to apply on messages. See docker api.
        :return: an iterable that contains events from docker. See the docker api for content.
        """
        if filters is None:
            filters = {}
        return self._docker.events(decode=True, filters=filters)

class FixDockerSocket():  # pragma: no cover
    """
    Fix the API inconsistency of docker-py with attach_socket
    """
    def __init__(self, docker_py_sock):
        self.docker_py_sock = docker_py_sock

    def get_socket(self):
        """
        Returns a valid socket.socket object
        """
        try:
            return self.docker_py_sock._sock  # pylint: disable=protected-access
        except AttributeError:
            return self.docker_py_sock

    def close_socket(self):
        """
        Correctly closes the socket
        :return:
        """
        try:
            self.docker_py_sock._sock.close()  # pylint: disable=protected-access
        except AttributeError:
            pass
        self.docker_py_sock.close()
