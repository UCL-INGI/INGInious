""" Contains the Waiter class, which waits until completion of task run in a container """
import Queue
import json
import multiprocessing
import time

import docker


class Waiter(multiprocessing.Process):

    """
        Periodically call the distant docker to know which containers are done

        Take from the input_queue tuples with the form (jobid, containerid) and
        put in the output_queue tuples with the form (docker_instanceid, jobid, result)

    """

    def __init__(self, docker_instanceid, input_queue, output_queue, docker_configuration):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self._docker_configuration = docker_configuration
        self._docker_instanceid = docker_instanceid
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._waiting_jobs = {}
        self._docker = docker.Client(base_url=docker_configuration.get('server_url'))

    def run(self):
        while True:
            time.sleep(self._docker_configuration.get("time_between_polls", 0.5))
            # Empty the queue
            empty = False
            while not empty:
                try:
                    jobid, containerid = self._input_queue.get(False)
                    print "Waiter received jobid {} with containerid {}".format(jobid, containerid)
                    if containerid is None:
                        # an error occured
                        self._output_queue.put({"result": "crash", "text": "Unable to start the task verification"})
                    else:
                        self._waiting_jobs[containerid] = jobid
                except Queue.Empty:
                    empty = True
                except EOFError:
                    empty = True

            # Query the running containers
            try:
                running_containers = [container["Id"] for container in self._docker.containers()]
                jobs_done = {containerid: jobid for containerid, jobid in self._waiting_jobs.iteritems() if containerid not in running_containers}
                self._waiting_jobs = {containerid: jobid for containerid, jobid in self._waiting_jobs.iteritems() if containerid in running_containers}
            except:
                continue

            for containerid, jobid in jobs_done.iteritems():
                try:
                    print "Container {} for jobid {} ended".format(containerid, jobid)
                    stdout = str(self._docker.logs(containerid, stdout=True, stderr=False))
                    stderr = str(self._docker.logs(containerid, stdout=False, stderr=True))
                    if stderr != "":
                        print "STDERR: " + stderr
                    # Delete used containers to avoid using too much disk space
                    self._docker.remove_container(containerid, True, False, True)
                    result = json.loads(stdout)
                    print "Sent result to callback manager for jobid {}".format(jobid)
                    self._output_queue.put((self._docker_instanceid, jobid, result))
                except:
                    print "No result for jobid {} after container run".format(jobid)
                    self._output_queue.put((self._docker_instanceid, jobid, {"result": "crash", "text": "No output given by the task. Please contact an administrator if this problem reoccurs."}))
