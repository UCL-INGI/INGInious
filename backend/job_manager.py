""" Contains the class JobManager """
import multiprocessing
import os
import threading
import uuid

from backend._callback_manager import CallbackManager
from backend._container_image_creator import ContainerImageCreator
from backend._submitter import submitter
from backend._waiter import Waiter


class JobManager(object):

    """ Manages jobs """

    def __init__(self, docker_instances, containers_directory, tasks_directory, callback_manager_count=1, submitter_count=None):
        """
            Starts a job manager.

            Arguments:

            *docker_instances*
                A list of dictionaries containing information about a distant docker daemon:
                ::

                    {
                        server_url: "the url to the docker daemon. May be a UNIX socket. Mandatory",
                        container_prefix: "The prefix to be used on container names. by default, it is 'inginious/'",
                        waiters: 1,
                        time_between_polls: 0.5,
                        max_concurrent_jobs: 100,
                        build_containers_on_start: false
                    }

                *waiters* is an integer indicating the number of waiters processes to start for this docker instance.
                *time_between_polls* is an integer in seconds. It is the time between two polls on the distant docker
                daemon to see if the job is done

            *containers_directory*
                The local directory path containing the Dockerfiles

            *tasks_directory*
                The local directory path containing the courses and the tasks

            *submitter_count*
                Size of the submitter pool. Default the the number of processors

            *callback_manager_count*
                Number of thread to launch to handle the callbacks

            A job manager manages, in fact, pools of processes called submitters and waiters.

            The first pool, containing the submitters, launch *submitter_count* processes.
            If *submitter_count* = None, it launches the amount of processors available.
            Submitters are in charge of starting the (maybe distant) docker containers.

            The second pool contains a number of waiters (the number is defined by each docker instance's configuration)
            that *wait* for a job to end on the distant docker daemon. Starting more than one process per docker instance is most of the time useless.

            NB: in fact, the *waiters* pool is not a python multiprocessing.Pool object.

            The job manager also launch a number of thread to handle the callbacks (the number is given by callback_manager_count)
        """
        self._containers_directory = containers_directory
        self._tasks_directory = tasks_directory

        self._memory_manager = multiprocessing.Manager()

        print "Starting the submitter pool"
        self._submitter_pool = multiprocessing.Pool(submitter_count)

        self._docker_waiter_queues = []
        self._docker_waiter_processes = []

        self._done_queue = self._memory_manager.Queue()

        #_running_job_count is only used by the current process, but needs to be locked
        self._running_job_count = []
        self._running_job_count_lock = threading.Lock()
        self._running_job_data = {}

        self._docker_config = docker_instances

        # Start waiters
        print "Starting waiters and container image builders"
        builders = []
        for docker_instance_id, docker_config in enumerate(self._docker_config):

            docker_instance_queue = self._memory_manager.Queue()
            self._docker_waiter_queues.append(docker_instance_queue)

            processes = []
            for i in range(docker_config.get("waiters", 1)):
                print "Starting waiter {} from docker instance {}".format(i, docker_instance_id)
                process = Waiter(docker_instance_id, docker_instance_queue, self._done_queue, docker_config)
                process.start()
                processes.append(process)

            if docker_config.get("build_containers_on_start", False):
                print "Starting image builder for docker instance {}".format(docker_instance_id)
                process = ContainerImageCreator(docker_instance_id, docker_config, self._containers_directory, self.get_container_names())
                process.start()
                builders.append(process)

            self._docker_waiter_processes.append(processes)
            self._running_job_count.append(0)

        if len(builders):
            print "Waiting for builders to end"
            for builder in builders:
                builder.join()
            print "Builders ended"

        # Start callback managers
        print "Starting callback managers"
        self._callback_manager = []
        for _ in range(callback_manager_count):
            process = CallbackManager(self._done_queue, self._running_job_data, self._running_job_count, self._running_job_count_lock)
            self._callback_manager.append(process)
            process.start()

        print "Job Manager initialization done"

    def get_waiting_jobs_count(self):
        """Returns the total number of waiting jobs in the Job Manager"""
        self._running_job_count_lock.acquire()
        result = 0
        for item in self._running_job_count:
            result += item
        self._running_job_count_lock.release()
        return item

    def _get_docker_instance_and_inc(self):
        """ Return the id of a docker instance and increment the job count associated """
        self._running_job_count_lock.acquire()
        available_instances = [
            (entry, count) for entry, count in enumerate(
                self._running_job_count) if self._docker_config[entry].get(
                "q", 100) == 0 or self._docker_config[entry].get(
                "max_concurrent_jobs", 100) > count]
        if not len(available_instances):
            self._running_job_count_lock.release()
            return None
        min_index, min_value = min(available_instances, key=lambda p: p[1])
        self._running_job_count[min_index] = min_value + 1
        self._running_job_count_lock.release()
        return min_index

    def new_job(self, task, inputdata, callback):
        """ Add a new job. callback is a function that will be called asynchronously in the job manager's process. """
        jobid = uuid.uuid4()

        # Base dictonnary with output
        basedict = {"task": task, "input": inputdata}

        # Check task answer that do not need emulation
        first_result, need_emul, first_text, first_problems, multiple_choice_error_count = task.check_answer(inputdata)
        basedict.update({"result": ("success" if first_result else "failed")})
        if first_text is not None:
            basedict["text"] = first_text
        if first_problems:
            basedict["problems"] = first_problems
        if multiple_choice_error_count != 0:
            basedict["text"].append("You have {} errors in the multiple choice questions".format(multiple_choice_error_count))

        if need_emul:
            # Go through the whole process: sent everything to docker
            docker_instance = self._get_docker_instance_and_inc()

            if docker_instance is None:
                self._done_queue.put((None, jobid, {"result": "crash", "text": "INGInious is over-capacity. Please try again later."}))
            else:
                self._running_job_data[jobid] = (task, callback, basedict)

                self._submitter_pool.apply_async(
                    submitter, [jobid, inputdata,
                                os.path.join(self._tasks_directory, task.get_course_id(), task.get_id()),
                                task.get_limits(),
                                task.get_environment(),
                                self._docker_config[docker_instance],
                                self._docker_waiter_queues[docker_instance]])
        else:
            # Only send data to a CallbackManager
            basedict["text"] = "\n".join(basedict["text"])
            self._running_job_data[jobid] = (task, callback, basedict)
            self._done_queue.put((None, jobid, None))

        return jobid

    def get_container_names(self):
        """ Returns available containers """
        containers = [
            f for f in os.listdir(
                self._containers_directory) if os.path.isdir(
                os.path.join(
                    self._containers_directory,
                    f)) and os.path.isfile(
                    os.path.join(
                        self._containers_directory,
                        f,
                        "Dockerfile"))]

        return containers
