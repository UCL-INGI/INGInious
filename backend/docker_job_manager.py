""" Contains method to manage the Docker containers """
import json
import os

import docker

from backend.job_manager import JobManager


class DockerJobManager (JobManager):

    """ Send jobs to Docker """

    def __init__(self, jobqueue, server_url, tasks_directory, containers_directory, container_prefix):
        JobManager.__init__(self, jobqueue)
        self._docker = docker.Client(base_url=server_url)
        self._server_url = server_url
        self.tasks_directory = tasks_directory
        self.container_prefix = container_prefix
        self.containers_directory = containers_directory

    def get_sockets(self, containerid):
        """ Utility function to get stdin of a container """
        return self._docker.attach_socket(containerid, {'stdin': 1, 'stream': 1})

    def run_job(self, jobid, task, inputdata):
        """ Runs the job by launching a container """
        # limits: currently we only supports time and memory limits.
        # Memory is the memory used by the VM, in megabytes, and time is the time taken by the script (not the VM!) in seconds
        mem_limit = task.get_limits()["memory"]
        if mem_limit < 20:
            mem_limit = 20
        elif mem_limit > 500:
            mem_limit = 500

        response = self._docker.create_container(
            self.container_prefix + task.get_environment(),
            stdin_open=True,
            network_disabled=True,
            volumes={'/ro/task': {}},
            mem_limit=mem_limit * 1024 * 1024
        )
        container_id = response["Id"]
        self._docker.start(container_id, binds={os.path.abspath(os.path.join(self.tasks_directory, task.get_course_id(), task.get_id())): {'ro': True, 'bind': '/ro/task'}})
        self.get_sockets(container_id).send(json.dumps(inputdata) + "\n")
        self._docker.wait(container_id)
        # Get the std outputs
        stdout = str(self._docker.logs(container_id, stdout=True, stderr=False))
        stderr = str(self._docker.logs(container_id, stdout=False, stderr=True))
        if stderr != "":
            print "STDERR: " + stderr
        # Delete used containers to avoid using too much disk space
        self._docker.remove_container(container_id, True, False, True)
        return json.loads(stdout)

    def build_docker_container(self, container):
        """ Ensures a container is up to date """
        response = self._docker.build(path=os.path.join(self.containers_directory, container), tag=self.container_prefix + container, rm=True)
        for i in response:
            if i == "\n" or i == "\r\n":
                continue
            try:
                j = json.loads(i)
            except:
                raise Exception("Error while building " + container + ": can't read Docker output")
            if 'error' in j:
                raise Exception("Error while building " + container + ": Docker returned error" + j["error"])

    @classmethod
    def get_container_names(cls, container_directory, with_prefix=None):
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

        containers = self.get_container_names(self.containers_directory)
        for container in containers:
            print "\tbuilding " + container
            try:
                self.build_docker_container(container)
            except Exception as inst:
                print "\tthere was an error while building the container:"
                print "\t\t" + str(inst)
        print "- Containers have been built"
