# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import asyncio
import logging
import uuid
from abc import abstractmethod, ABCMeta

import time

from inginious.client._zeromq_client import BetterParanoidPirateClient
from inginious.common.messages import ClientHello, BackendUpdateContainers, BackendBatchJobDone, BackendBatchJobStarted, BackendJobStarted, \
    BackendJobDone, BackendJobSSHDebug, ClientNewBatchJob, ClientNewJob, ClientKillJob, ClientGetQueue, BackendGetQueue


def _callable_once(func):
    """ Returns a function that is only callable once; any other call will do nothing """

    def once(*args, **kwargs):
        if not once.called:
            once.called = True
            return func(*args, **kwargs)

    once.called = False
    return once


class AbstractClient(object, metaclass=ABCMeta):
    @abstractmethod
    def start(self):
        """ Starts the Client. Should be done after a complete initialisation of the hook manager. """
        pass

    @abstractmethod
    def close(self):
        """ Close the Client """
        pass

    @abstractmethod
    def get_batch_containers_metadata(self):
        """
            Returns the arguments needed by a particular batch container (cached version)
            :returns: a dict of dict in the form
                {
                    "container title": {
                        "container description in restructuredtext",
                        {
                            "key":
                            {
                                "type:" "file", #or "text",
                                "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                                "name": "name of the field", #not mandatory in file, default "key"
                                "description": "a short description of what this field is used for", #not mandatory, default ""
                                "custom_key1": "custom_value1",
                                ...
                            }
                        }
                    }
                }
        """
        pass

    @abstractmethod
    def get_available_containers(self):
        """
        Return the list of available containers for grading
        """
        pass

    @abstractmethod
    def new_job(self, task, inputdata, callback, launcher_name="Unknown", debug=False, ssh_callback=None):
        """ Add a new job. Every callback will be called once and only once.

        :type task: Task
        :param inputdata: input from the student
        :type inputdata: Storage or dict
        :param callback: a function that will be called asynchronously in the client's process, with the results.
            it's signature must be (result, grade, problems, tests, custom, archive), where:
            result is itself a tuple containing the result string and the main feedback (i.e. ('success', 'You succeeded');
            grade is a number between 0 and 100 indicating the grade of the users;
            problems is a dict of tuple, in the form {'problemid': result};
            test is a dict of tests made in the container
            custom is a dict containing random things set in the container
            archive is either None or a bytes containing a tgz archive of files from the job
        :type callback: __builtin__.function or __builtin__.instancemethod
        :param launcher_name: for informational use
        :type launcher_name: str
        :param debug: Either True(outputs more info), False(default), or "ssh" (starts a remote ssh server. ssh_callback needs to be defined)
        :type debug: bool or string
        :param ssh_callback: a callback function that will be called with (host, port, password), the needed credentials to connect to the
                             remote ssh server. May be called with host, port, password being None, meaning no session was open.
        :type ssh_callback: __builtin__.function or __builtin__.instancemethod or None
        :return: the new job id
        """
        pass

    @abstractmethod
    def new_batch_job(self, container_name, inputdata, callback, launcher_name="Unknown"):
        """ Add a new batch job. callback is a function that will be called asynchronously in the client's process.
            inputdata is a dict containing all the keys of get_batch_containers_metadata()[container_name]["parameters"].
            The values associated are file-like objects for "file" types and  strings for "text" types.
        """
        pass

    @abstractmethod
    def kill_job(self, job_id):
        """
        Kills a running job
        :param job_id:
        """
        pass

    @abstractmethod
    def get_job_queue_snapshot(self):
        """ Get a snapshot of the remote backend job queue. May be a cached version.
            May not contain recent jobs. May return None if no snapshot is available

        Return a tuple of two lists (or None, None):
        jobs_running: a list of tuples in the form
            (job_id, is_current_client_job, is_batch, info, launcher, started_at, max_end)
            where
            - job_id is a job id. It may be from another client.
            - is_current_client_job is a boolean indicating if the client that asked the request has started the job
            - agent_name is the agent name
            - is_batch is True if the job is a batch job, false else
            - info is either the batch container name if is_batch is True, or "courseid/taskid"
            - launcher is the name of the launcher, which may be anything
            - started_at the time (in seconds since UNIX epoch) at which the job started
            - max_end the time at which the job will timeout (in seconds since UNIX epoch), or -1 if no timeout is set
        jobs_waiting: a list of tuples in the form
            (job_id, is_current_client_job, is_batch, info, launcher, max_time)
            where
            - job_id is a job id. It may be from another client.
            - is_current_client_job is a boolean indicating if the client that asked the request has started the job
            - is_batch is True if the job is a batch job, false else
            - info is either the batch container name if is_batch is True, or "courseid/taskid"
            - launcher is the name of the launcher, which may be anything
            - max_time the maximum time that can be used, or -1 if no timeout is set
        """
        pass

    @abstractmethod
    def get_job_queue_info(self, jobid):
        """
        :param jobid: the jobid of a *task*.
        :return: If the submission is in the queue, then returns a tuple (nb tasks before running (or -1 if running), approx wait time in seconds)
                 Else, returns None
        """
        pass

class Client(BetterParanoidPirateClient):
    def __init__(self, context, backend_addr, queue_update = 10):
        """
        Init a new RRR.
        :param context: 0MQ context
        :param backend_addr: 0MQ address of the backend
        :param queue_update: interval in seconds between two updates of the distant queue. Set to something <= 0 to disable updates.
        """
        super().__init__(context, backend_addr)
        self._logger = logging.getLogger("inginious.client")
        self._available_containers = []
        self._available_batch_containers = []

        self._register_handler(BackendUpdateContainers, self._handle_update_containers)
        self._register_handler(BackendGetQueue, self._handle_job_queue_update)
        self._register_transaction(ClientNewBatchJob, BackendBatchJobDone, self._handle_batch_job_done, self._handle_batch_job_abort,
                                   lambda x: x.job_id, [
                                       (BackendBatchJobStarted, self._handle_batch_job_started)
                                   ])
        self._register_transaction(ClientNewJob, BackendJobDone, self._handle_job_done, self._handle_job_abort,
                                   lambda x: x.job_id, [
                                       (BackendJobStarted, self._handle_job_started),
                                       (BackendJobSSHDebug, self._handle_job_ssh_debug)
                                   ])

        self._queue_update_timer = queue_update
        self._queue_update_last_attempt = 0              # nb of time we waited _queue_update_timer seconds for a reply
        self._queue_update_last_attempt_max = 3
        self._queue_cache = None
        self._queue_job_cache = {} #format is job_id: (nb_tasks_before (can be -1 == running), approx_wait_time_in_seconds)

    async def _ask_queue_update(self):
        """ Send a ClientGetQueue message to the backend, if one is not already sent """
        try:
            while True:
                await asyncio.sleep(self._queue_update_timer)
                if self._queue_update_last_attempt == 0 or self._queue_update_last_attempt > self._queue_update_last_attempt_max:
                    if self._queue_update_last_attempt:
                        self._logger.error("Asking for a job queue update despite previous update not yet received")
                    else:
                        self._logger.debug("Asking for a job queue update")

                    self._queue_update_last_attempt = 1
                    await self._simple_send(ClientGetQueue())
                else:
                    self._logger.error("Not asking for a job queue update as previous update not yet received")
        except asyncio.CancelledError:
            return
        except KeyboardInterrupt:
            return

    async def _handle_job_queue_update(self, message: BackendGetQueue):
        """ Handles a BackendGetQueue containing a snapshot of the job queue """
        self._logger.debug("Received job queue update")
        self._queue_update_last_attempt = 0
        self._queue_cache = message

        # Do some precomputation
        new_job_queue_cache = {}
        # format is job_id: (nb_jobs_before, max_remaining_time)
        for (job_id, is_local, _, is_batch, _2, _3, _4, max_end) in message.jobs_running:
            if is_local and not is_batch:
                new_job_queue_cache[job_id] = (-1, max_end - time.time())
        wait_time = 0
        nb_tasks = 0
        for (job_id, is_local, is_batch, _, _2, timeout) in message.jobs_waiting:
            if timeout > 0:
                wait_time += timeout
            if is_local and not is_batch:
                new_job_queue_cache[job_id] = (nb_tasks, wait_time)
            nb_tasks += 1

        self._queue_job_cache = new_job_queue_cache

    def get_job_queue_snapshot(self):
        if self._queue_cache is not None:
            return self._queue_cache.jobs_running, self._queue_cache.jobs_waiting
        return None, None

    def get_job_queue_info(self, jobid):
        return self._queue_job_cache.get(jobid)

    async def _handle_update_containers(self, message: BackendUpdateContainers):
        self._available_batch_containers = message.available_batch_containers
        self._available_containers = message.available_containers
        self._logger.info("Updated containers and batch containers")
        self._logger.debug("Containers: %s", str(self._available_containers))
        self._logger.debug("Batch containers: %s", str(self._available_batch_containers))

    async def _handle_batch_job_started(self, message: BackendBatchJobStarted, **kwargs):  # pylint: disable=unused-argument
        self._logger.debug("Batch job %s started", message.job_id)

    async def _handle_batch_job_done(self, message: BackendBatchJobDone, callback):
        self._logger.debug("Batch job %s done", message.job_id)

        # Call the callback
        try:
            callback(message.retval, message.stdout, message.stderr, message.file)
        except Exception as e:
            self._logger.exception("Failed to call the callback function for jobid %s: %s", message.job_id, repr(e), exc_info=True)

    async def _handle_job_started(self, message: BackendJobStarted, **kwargs):  # pylint: disable=unused-argument
        self._logger.debug("Job %s started", message.job_id)

    async def _handle_job_done(self, message: BackendJobDone, task, callback, ssh_callback):  # pylint: disable=unused-argument
        self._logger.debug("Job %s done", message.job_id)
        job_id = message.job_id

        # Ensure ssh_callback is called at least once
        try:
            # NB: original ssh_callback was wrapped with _callable_once
            await self._loop.run_in_executor(None, lambda: ssh_callback(None, None, None))
        except:
            self._logger.exception("Error occurred while calling ssh_callback for job %s", job_id)

        # Call the callback
        try:
            callback(message.result, message.grade, message.problems, message.tests, message.custom, message.archive, message.stdout, message.stderr)
        except Exception as e:
            self._logger.exception("Failed to call the callback function for jobid %s: %s", job_id, repr(e), exc_info=True)

    async def _handle_job_ssh_debug(self, message: BackendJobSSHDebug, ssh_callback, **kwargs):  # pylint: disable=unused-argument
        try:
            await self._loop.run_in_executor(None, lambda: ssh_callback(message.host, message.port, message.password))
        except:
            self._logger.exception("Error occurred while calling ssh_callback for job %s", message.job_id)

    async def _handle_batch_job_abort(self, job_id: str, callback):
        await self._handle_batch_job_done(BackendBatchJobDone(job_id, -1, "Backend unavailable, retry later", "", None), callback)

    async def _handle_job_abort(self, job_id: str, task, callback, ssh_callback):
        await self._handle_job_done(BackendJobDone(job_id, ("crash", "Backend unavailable, retry later"), 0.0, {}, {}, {}, None, "", ""), task, callback,
                                    ssh_callback)

    async def _on_disconnect(self):
        self._logger.warning("Disconnected from backend, retrying...")

    async def _on_connect(self):
        self._available_containers = []
        self._available_batch_containers = []
        await self._simple_send(ClientHello("me"))
        self._restartable_tasks.append(self._loop.create_task(self._ask_queue_update()))
        self._logger.info("Connecting to backend")

    def start(self):
        """ Starts the Client. Should be done after a complete initialisation of the hook manager. """
        self._loop.call_soon_threadsafe(asyncio.ensure_future, self.client_start())

    def close(self):
        """ Close the Client """
        pass

    def get_batch_containers_metadata(self):
        """
            Returns the arguments needed by a particular batch container (cached version)
            :returns: a dict of dict in the form
                {
                    "container title": {
                        "container description in restructuredtext",
                        {
                            "key":
                            {
                                "type:" "file", #or "text",
                                "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                                "name": "name of the field", #not mandatory in file, default "key"
                                "description": "a short description of what this field is used for", #not mandatory, default ""
                                "custom_key1": "custom_value1",
                                ...
                            }
                        }
                    }
                }
        """
        return self._available_batch_containers

    def get_available_containers(self):
        """
        Return the list of available containers for grading
        """
        return self._available_containers

    def new_job(self, task, inputdata, callback, launcher_name="Unknown", debug=False, ssh_callback=None):
        """ Add a new job. Every callback will be called once and only once.

        :type task: Task
        :param inputdata: input from the student
        :type inputdata: Storage or dict
        :param callback: a function that will be called asynchronously in the client's process, with the results.
            it's signature must be (result, grade, problems, tests, custom, archive), where:
            result is itself a tuple containing the result string and the main feedback (i.e. ('success', 'You succeeded');
            grade is a number between 0 and 100 indicating the grade of the users;
            problems is a dict of tuple, in the form {'problemid': result};
            test is a dict of tests made in the container
            custom is a dict containing random things set in the container
            archive is either None or a bytes containing a tgz archive of files from the job
        :type callback: __builtin__.function or __builtin__.instancemethod
        :param launcher_name: for informational use
        :type launcher_name: str
        :param debug: Either True(outputs more info), False(default), or "ssh" (starts a remote ssh server. ssh_callback needs to be defined)
        :type debug: bool or string
        :param ssh_callback: a callback function that will be called with (host, port, password), the needed credentials to connect to the
                             remote ssh server. May be called with host, port, password being None, meaning no session was open.
        :type ssh_callback: __builtin__.function or __builtin__.instancemethod or None
        :return: the new job id
        """
        job_id = str(uuid.uuid4())

        if debug == "ssh" and ssh_callback is None:
            self._logger.error("SSH callback not set in %s/%s", task.get_course_id(), task.get_id())
            callback(("crash", "SSH callback not set."), 0.0, {}, {}, {}, None, "", "")
            return
        # wrap ssh_callback to ensure it is called at most once, and that it can always be called to simplify code
        ssh_callback = _callable_once(ssh_callback if ssh_callback is not None else lambda _1, _2, _3: None)

        environment = task.get_environment()
        if environment not in self._available_containers:
            self._logger.warning("Env %s not available for task %s/%s", environment, task.get_course_id(), task.get_id())
            ssh_callback(None, None, None)  # ssh_callback must be called once
            callback(("crash", "Environment not available."), 0.0, {}, {}, {}, None, "", "")
            return

        enable_network = task.allow_network_access_grading()

        try:
            limits = task.get_limits()
            time_limit = int(limits.get('time', 20))
            hard_time_limit = int(limits.get('hard_time', 3 * time_limit))
            mem_limit = int(limits.get('memory', 200))
        except:
            self._logger.exception("Cannot retrieve limits for task %s/%s", task.get_course_id(), task.get_id())
            ssh_callback(None, None, None)  # ssh_callback must be called once
            callback(("crash", "Error while reading task limits"), 0.0, {}, {}, {}, None, "", "")
            return

        msg = ClientNewJob(job_id, task.get_course_id(), task.get_id(), inputdata, environment, enable_network, time_limit,
                           hard_time_limit, mem_limit, debug, launcher_name)
        self._loop.call_soon_threadsafe(asyncio.ensure_future, self._create_transaction(msg, task=task, callback=callback,
                                                                                        ssh_callback=ssh_callback))

        return job_id

    def new_batch_job(self, container_name, inputdata, callback, launcher_name="Unknown"):
        """ Add a new batch job. callback is a function that will be called asynchronously in the client's process.
            inputdata is a dict containing all the keys of get_batch_containers_metadata()[container_name]["parameters"].
            The values associated are file-like objects for "file" types and  strings for "text" types.
        """
        job_id = str(uuid.uuid4())

        # Verify inputdata
        if container_name not in self._available_batch_containers:
            raise Exception("Invalid container")

        batch_args = self._available_batch_containers[container_name]["parameters"]
        if set(inputdata.keys()) != set(batch_args.keys()):
            raise Exception("Invalid keys for inputdata")
        for key in batch_args:
            if batch_args[key]["type"] == "text" and not isinstance(inputdata[key], str):
                raise Exception("Invalid value for inputdata: the value for key {} should be a string".format(key))
            elif batch_args[key]["type"] == "file" and isinstance(inputdata[key], str):
                raise Exception("Invalid value for inputdata: the value for key {} should be a file object".format(key))

        msg = ClientNewBatchJob(job_id, container_name, inputdata, launcher_name)
        self._loop.call_soon_threadsafe(asyncio.ensure_future, self._create_transaction(msg, callback=callback))

        return job_id

    def kill_job(self, job_id):
        """
        Kills a running job
        """
        self._loop.call_soon_threadsafe(asyncio.ensure_future, self._simple_send(ClientKillJob(job_id)))
