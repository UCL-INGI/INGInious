""" Contains the class JobManager """
import multiprocessing
import os
import uuid

from backend._callback_manager import CallbackManager
from backend._message_types import RUN_JOB
import backend._pool_manager


class JobManager(object):

    """ Manages jobs """

    def __init__(self, docker_instances, containers_directory, tasks_directory, callback_manager_count=1, slow_pool_size=None, fast_pool_size=None):
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

            *process_pool_size*
                Size of the process pool which runs the submit and delete action. Default: number of processors

            *callback_manager_count*
                Number of thread to launch to handle the callbacks

            A job manager manages, in fact, pools of processes called submitters and waiters.

            The first pool, which runs two actions: submit and delete, launches *process_pool_size* processes.
            If *process_pool_size* = None, it launches the amount of processors available.
            The submit and delete actions respectively starts or delete a docker container.

            The second pool contains a number of waiters (the number is defined by each docker instance's configuration)
            that *wait* for a job to end on the distant docker daemon. Starting more than one process per docker instance is most of the time useless.

            NB: in fact, the *waiters* pool is not a Python *multiprocessing.Pool* object.

            The job manager also launch a number of thread to handle the callbacks (the number is given by callback_manager_count)
        """
        self._containers_directory = containers_directory
        self._tasks_directory = tasks_directory
        self._docker_config = docker_instances

        self._memory_manager = multiprocessing.Manager()
        self._operations_queue = self._memory_manager.Queue()
        self._done_queue = self._memory_manager.Queue()

        self._running_job_data = {}

        # Correct the size of the slow pool size, which will contain all waiters
        if (multiprocessing.cpu_count() if slow_pool_size is None else slow_pool_size) < len(self._docker_config) + 1:
            slow_pool_size = len(self._docker_config) + 1

        # Start the pool manager
        self._pool_manager = backend._pool_manager.PoolManager(self._operations_queue, self._done_queue, docker_instances, containers_directory, tasks_directory, fast_pool_size, slow_pool_size)
        self._pool_manager.start()

        # Start callback managers
        print "Starting callback managers"
        self._callback_manager = []
        for _ in range(callback_manager_count):
            process = CallbackManager(self._done_queue, self._docker_config, self._running_job_data)
            self._callback_manager.append(process)
            process.start()

        print "Job Manager initialization done"

    def get_waiting_jobs_count(self):
        """Returns the total number of waiting jobs in the Job Manager"""
        return len(self._running_job_data)

    def new_job(self, task, inputdata, callback):
        """ Add a new job. callback is a function that will be called asynchronously in the job manager's process. """
        jobid = uuid.uuid4()

        # Base dictionary with output
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
            self._running_job_data[jobid] = (task, callback, basedict)
            self._operations_queue.put((RUN_JOB, [jobid, inputdata, os.path.join(self._tasks_directory, task.get_course_id(), task.get_id()), task.get_limits(), task.get_environment()]))
        else:
            # Only send data to a CallbackManager
            basedict["text"] = "\n".join(basedict["text"])
            self._running_job_data[jobid] = (task, callback, basedict)
            self._done_queue.put((jobid, None))

        return jobid

    @staticmethod
    def get_container_names(containers_directory):
        """ Returns available containers """
        containers = [
            f for f in os.listdir(
                containers_directory) if os.path.isdir(
                os.path.join(
                    containers_directory,
                    f)) and os.path.isfile(
                    os.path.join(
                        containers_directory,
                        f,
                        "Dockerfile"))]

        return containers
