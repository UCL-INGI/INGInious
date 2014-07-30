""" Contains the class ContainerImageCreator, which is used by JobManager to build new container image on a docker instance """

import json
import multiprocessing
import os
import docker


class ContainerImageCreator(multiprocessing.Process):

    """ Builds new container image on a docker instance """

    def __init__(self, docker_instance_id, docker_configuration, containers_directory):
        multiprocessing.Process.__init__(self)
        self._conf = docker_configuration
        self._containers_directory = containers_directory
        self._docker_instance_id = docker_instance_id

    def run(self):
        self.build_all_docker_containers()

    def build_docker_container(self, container):
        """ Ensures a container is up to date """
        docker_connection = docker.Client(base_url=self._conf.get('server_url'))
        response = docker_connection.build(path=os.path.join(self._containers_directory, container), tag=self._conf.get("container_prefix", "inginious/") + container, rm=True)
        for i in response:
            if i == "\n" or i == "\r\n":
                continue
            try:
                j = json.loads(i)
            except:
                raise Exception("Error while building {} for docker instance {}: can't read Docker output".format(container, self._docker_instance_id))
            if 'error' in j:
                raise Exception("Error while building {} for docker instance {}: Docker returned error {}".format(container, self._docker_instance_id, j["error"]))

    def get_container_names(self, container_directory, with_prefix=None):
        """ Returns available containers """
        containers = [
            f for f in os.listdir(
                container_directory) if os.path.isdir(
                os.path.join(
                    container_directory,
                    f)) and os.path.isfile(
                    os.path.join(
                        container_directory,
                        f,
                        "Dockerfile"))]

        if with_prefix:
            containers = [with_prefix + f for f in containers]
        return containers

    def build_all_docker_containers(self):
        """ Ensures all containers are up to date """
        print "- Building containers"

        containers = self.get_container_names(self._containers_directory)
        for container in containers:
            print "\tbuilding container {} for docker instance {}".format(container, self._docker_instance_id)
            try:
                self.build_docker_container(container)
            except Exception as inst:
                print "\tthere was an error while building the container {} for docker instance {}:\n\t\t{}".format(container, self._docker_instance_id, str(inst))
        print "- Containers have been built"
