""" Contains the function _event_reader, which returns when containers are done. """
import json

import docker

from backend._message_types import CONTAINER_DONE


def event_reader(docker_instance_id, docker_config, output_queue):
    """ Read the event stream of docker to detect containers that have done their work """
    print "Event reader for instance {} started".format(docker_instance_id)
    docker_connection = docker.Client(base_url=docker_config.get('server_url'))
    for event in docker_connection.events():
        try:
            event = json.loads(event)
            if event.get("status") == "die":
                output_queue.put((CONTAINER_DONE, [docker_instance_id, event.get("id")]))
        except:
            print "Cannot read docker event {}".format(event)
