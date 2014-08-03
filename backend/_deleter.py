""" Contains the function deleter, which is used by PoolManager to delete a docker container """
import docker


def deleter(docker_config, containerid):
    """ Deletes a container """
    try:
        docker_connection = docker.Client(base_url=docker_config.get('server_url'))
        docker_connection.remove_container(containerid, True, False, True)
    except Exception as e:
        print "Cannot delete container {}: {}".format(containerid, repr(e))
