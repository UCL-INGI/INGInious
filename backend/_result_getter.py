""" Contains result_getter, which retrieves the result of a container """
import json

import docker

from backend._message_types import JOB_RESULT


def result_getter(jobid, containerid, docker_config, output_queue):
    """ Gets the results from a container """
    docker_connection = docker.Client(base_url=docker_config.get('server_url'))
    stdout = str(docker_connection.logs(containerid, stdout=True, stderr=False))
    stderr = str(docker_connection.logs(containerid, stdout=False, stderr=True))
    if stderr != "":
        print "STDERR: " + stderr
    result = json.loads(stdout)
    output_queue.put((JOB_RESULT, [jobid, result]))
