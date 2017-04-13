# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
from typing import Dict, Optional, Any, Union, Tuple, List

from inginious.common.message_meta import MessageMeta

# JobId of the backend, composed with the adress of the client and the client job id
BackendJobId = Tuple[bytes, str]
ClientJobId = str
SPResult = Tuple[str, str]


#################################################################
#                                                               #
#                      Client to Backend                        #
#                                                               #
#################################################################


class ClientHello(metaclass=MessageMeta, msgtype="client_hello"):
    """
        Let the client say hello to the backend (and thus register to some events)
    """

    def __init__(self, name: str):
        """
        :param name: name of the client (do not need to be unique)
        """
        self.name = name


class ClientNewBatchJob(metaclass=MessageMeta, msgtype="client_new_batch_job"):
    """
        Creates a new batch job.
        B->A.
        Agent should start the Batch Job, immediately send that the hob was created using BatchJobStarted.
        When the Batch Job ends, agent should send a BatchJobDone message.
    """

    def __init__(self, job_id: ClientJobId, container_name: str, input_data: Dict[str, Any], launcher: str):
        """
        :param job_id: the client-side job_id
        :param container_name: alias of the container to run
        :param input_data: the input data as a dict, fullfilling the parameters
        :param launcher: the name of the entity that launched this job, for logging purposes
        """
        self.job_id = job_id
        self.container_name = container_name
        self.input_data = input_data
        self.launcher = launcher


class ClientNewJob(metaclass=MessageMeta, msgtype="client_new_job"):
    """
        Creates a new job
        B->A.
    """

    def __init__(self, job_id: ClientJobId,
                 course_id: str, task_id: str, inputdata: Dict[str, Any],
                 environment: str, enable_network: bool, time_limit: int, hard_time_limit: Optional[int], mem_limit: int,
                 debug: Union[str, bool], launcher: str):
        """
        :param job_id: the client-side job id that is associated to this job
        :param course_id: course id of the task to run
        :param task_id: task id of the task to run
        :param inputdata: student input data
        :param environment: environment to use
        :param enable_network: wheter to enable the network or not, in supporting envs
        :param time_limit: timeout, in seconds, of the task, for supporting envs
        :param hard_time_limit: timeout, in seconds, of the task, for supporting envs. (hard)
        :param mem_limit: memory limit in Mo, for supporting envs.
        :param debug:
            True to enable debug
            False to disable it
            "ssh" to enable ssh debug
        :param launcher: the name of the entity that launched this job, for logging purposes
        """
        self.job_id = job_id
        self.course_id = course_id
        self.task_id = task_id
        self.inputdata = inputdata
        self.debug = debug
        self.environment = environment
        self.enable_network = enable_network
        self.time_limit = time_limit
        self.hard_time_limit = hard_time_limit
        self.mem_limit = mem_limit
        self.launcher = launcher


class ClientKillJob(metaclass=MessageMeta, msgtype="client_kill_job"):
    """
        Kills a running job.
        B->A.
    """

    def __init__(self, job_id: ClientJobId):
        """
        :param job_id: the client-side job id that is associated to the job to kill
        """
        self.job_id = job_id


class ClientGetQueue(metaclass=MessageMeta, msgtype="client_get_queue"):
    """
       Ask the backend to send the status of its job queue
    """

    def __init__(self): pass

#################################################################
#                                                               #
#                      Backend to Client                        #
#                                                               #
#################################################################


class BackendUpdateContainers(metaclass=MessageMeta, msgtype="backend_update_containers"):
    """
        Update the information about the containers on the client, from the informations retrieved from the agents
    """

    def __init__(self, available_containers: Tuple[str], available_batch_containers: Dict[str, Dict[str, str]]):
        """
            :param available_containers: list of available container aliases
            :param available_batch_containers: dict of available batch containers, in the format
                {
                    "name": {
                        "description": "a description written in RST",
                        "parameters": {
                            "key": {
                                 "type:" "file", #or "text",
                                 "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                                 "name": "name of the field", #not mandatory in file, default "key"
                                 "description": "a short description of what this field is used for" #not mandatory, default ""
                            }
                        }
                }
        """
        self.available_containers = available_containers
        self.available_batch_containers = available_batch_containers


class BackendBatchJobStarted(metaclass=MessageMeta, msgtype="backend_batch_job_started"):
    """
        Tell the backend the batch job asked with NewBatchJob has been created.
    """

    def __init__(self, job_id: ClientJobId):
        """
        :param job_id: the client-side job_id associated to the batch job
        """
        self.job_id = job_id


class BackendBatchJobDone(metaclass=MessageMeta, msgtype="backend_batch_job_done"):
    """
        Gives the results of a batch job to the backend
    """

    def __init__(self, job_id: ClientJobId, retval: int, stdout: str, stderr: str, file: Optional[bytes]):
        """
        :param job_id: the client-side job_id associated to the batch job
        :param retval:
            0 if everything went well
            -1 if the container failed to start
            1-255 if the container crashed (it is the return value of the main command of the batch job)
        :param stdout: stdout of the job
        :param stderr: stderr of the job
        :param file: tgz file (as a bytestring) of the content of the batch job container after completion, or None if an error occurred
        """
        self.job_id = job_id
        self.retval = retval
        self.stdout = stdout
        self.stderr = stderr
        self.file = file


class BackendJobStarted(metaclass=MessageMeta, msgtype="backend_job_started"):
    """
        Indicates to the backend that a job started
    """

    def __init__(self, job_id: ClientJobId):
        """
        :param job_id: the client-side job_id associated to the job
        """
        self.job_id = job_id


class BackendJobDone(metaclass=MessageMeta, msgtype="backend_job_done"):
    """
        Gives the result of a job.
    """

    def __init__(self, job_id: ClientJobId, result: SPResult, grade: float, problems: Dict[str, SPResult], tests: Dict[str, Any],
                 custom: Dict[str, Any], archive: Optional[bytes], stdout: Optional[str], stderr: Optional[str]):
        """
        :param job_id: the client-side job id associated with this job
        :param result: A tuple containing the result type and the text to be shown to the student
            Result type can be:
            - "killed": the container was killed externally (not really an error)
            - "crash": the container crashed (INGInious error)
            - "overflow": the container was killed due to a memory overflow (student/task writer error)
            - "timeout": the container was killed due to a timeout (student/task writer error)
            - "success": the student succeeded to resolve this task
            - "failed": the student failed to succeed this task
            - "error": an error happenned in the grading script (task writer error)
        :param grade: grade
        :param problems: particular feedbacks for each subproblem. Keys are subproblem ids.
        :param tests: tests made in the container
        :param custom: custom values
        :param archive: bytes string containing an archive of the content of the container as a tgz
        :param stdout: container stdout
        :param stderr: container stderr
        """
        self.job_id = job_id
        self.result = result
        self.grade = grade
        self.problems = problems
        self.tests = tests
        self.custom = custom
        self.archive = archive
        self.stdout = stdout
        self.stderr = stderr


class BackendJobSSHDebug(metaclass=MessageMeta, msgtype="backend_job_ssh_debug"):
    """
        Gives the necessary info to SSH into a job running in ssh debug mode
    """

    def __init__(self, job_id: ClientJobId, host: str, port: int, password: str):
        """
        :param job_id: the client-side job id associated with this job
        :param host: host to which the client should connect
        :param port: port on which sshd is bound
        :param password: password that allows to connect to the container
        """
        self.job_id = job_id
        self.host = host
        self.port = port
        self.password = password

class BackendGetQueue(metaclass=MessageMeta, msgtype="backend_get_queue"):
    """
        Send the status of the job queue to the client
    """
    def __init__(self, jobs_running: List[Tuple[ClientJobId, bool, str, bool, str, str, int, int]],
                       jobs_waiting: List[Tuple[ClientJobId, bool, bool, str, str, int]]):
        """
        :param jobs_running: a list of tuples in the form
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
        :param jobs_waiting: a list of tuples in the form
            (job_id, is_current_client_job, is_batch, info, launcher, max_time)
            where
            - job_id is a job id. It may be from another client.
            - is_current_client_job is a boolean indicating if the client that asked the request has started the job
            - is_batch is True if the job is a batch job, false else
            - info is either the batch container name if is_batch is True, or "courseid/taskid"
            - launcher is the name of the launcher, which may be anything
            - max_time the maximum time that can be used, or -1 if no timeout is set
        """
        self.jobs_running = jobs_running
        self.jobs_waiting = jobs_waiting

#################################################################
#                                                               #
#                      Backend to Agent                         #
#                                                               #
#################################################################


class BackendNewBatchJob(metaclass=MessageMeta, msgtype="backend_new_batch_job"):
    """
        Creates a new batch job.
        B->A.
        Agent should start the Batch Job, immediately send that the hob was created using BatchJobStarted.
        When the Batch Job ends, agent should send a BatchJobDone message.
    """

    def __init__(self, job_id: BackendJobId, container_name: str, input_data: Dict[str, Any]):
        """
        :param job_id: the backend-side job_id
        :param container_name: alias of the container to run
        :param input_data: input dict, fullfilling the parameters of the container
        """
        self.job_id = job_id
        self.container_name = container_name
        self.input_data = input_data


class BackendNewJob(metaclass=MessageMeta, msgtype="backend_new_job"):
    """
        Creates a new job
        B->A.
    """

    def __init__(self, job_id: BackendJobId, course_id: str, task_id: str, inputdata: Dict[str, Any],
                 environment: str, enable_network: bool, time_limit: int, hard_time_limit: Optional[int], mem_limit: int,
                 debug: Union[str, bool]):
        """
        :param job_id: the backend-side job id that is associated to this job
        :param course_id: course id of the task to run
        :param task_id: task id of the task to run
        :param inputdata: student input data
        :param environment: environment to use
        :param enable_network: wheter to enable the network or not, in supporting envs
        :param time_limit: timeout, in seconds, of the task, for supporting envs
        :param hard_time_limit: timeout, in seconds, of the task, for supporting envs. (hard)
        :param mem_limit: memory limit in Mo, for supporting envs.
        :param debug:
            True to enable debug
            False to disable it
            "ssh" to enable ssh debug
        """
        self.job_id = job_id
        self.course_id = course_id
        self.task_id = task_id
        self.inputdata = inputdata
        self.debug = debug
        self.environment = environment
        self.enable_network = enable_network
        self.time_limit = time_limit
        self.hard_time_limit = hard_time_limit
        self.mem_limit = mem_limit


class BackendKillJob(metaclass=MessageMeta, msgtype="backend_kill_job"):
    """
        Kills a running job.
        B->A.
    """

    def __init__(self, job_id: BackendJobId):
        """
        :param job_id: the backend-side job id that is associated to the job to kill
        """
        self.job_id = job_id


#################################################################
#                                                               #
#                      Agent to Backend                         #
#                                                               #
#################################################################


class AgentHello(metaclass=MessageMeta, msgtype="agent_hello"):
    """
        Let the agent say hello and announce which containers it has available
    """

    def __init__(self, friendly_name: str, available_job_slots: int, available_containers: Dict[str, Dict[str, str]],
                 available_batch_containers: Dict[str, Dict[str, Union[str, Dict[str, str]]]]):
        """
            :param friendly_name: a string containing a friendly name to identify agent
            :param available_job_slots: an integer giving the number of concurrent
            :param available_containers: dict of available containers
            {
                "name": {                          #for example, "default"
                    "id": "container img id",      #             "sha256:715c5cb5575cdb2641956e42af4a53e69edf763ce701006b2c6e0f4f39b68dd3"
                    "created": 12345678            # create date
                }
            }
            :param available_batch_containers: dict of available batch containers, in the format
                {
                    "name": {
                        "description": "a description written in RST",
                        "id": "container img id",
                        "created": 123456789
                        "parameters": {
                            "key": {
                                 "type:" "file", #or "text",
                                 "path": "path/to/file/inside/input/dir", #not mandatory in file, by default "key"
                                 "name": "name of the field", #not mandatory in file, default "key"
                                 "description": "a short description of what this field is used for" #not mandatory, default ""
                            }
                        }
                }
        """

        self.friendly_name = friendly_name
        self.available_job_slots = available_job_slots
        self.available_containers = available_containers
        self.available_batch_containers = available_batch_containers


class AgentBatchJobStarted(metaclass=MessageMeta, msgtype="agent_batch_job_started"):
    """
        Tell the backend the batch job asked with NewBatchJob has been created.
        A->B.
    """

    def __init__(self, job_id: BackendJobId):
        """
        :param job_id: the backend-side job_id associated to the batch job
        """
        self.job_id = job_id


class AgentBatchJobDone(metaclass=MessageMeta, msgtype="agent_batch_job_done"):
    """
        Gives the results of a batch job to the backend
        A->B.
    """

    def __init__(self, job_id: BackendJobId, retval: int, stdout: str, stderr: str, file: Optional[bytes]):
        """
        :param job_id: the backend-side job_id associated to the batch job
        :param retval:
            0 if everything went well
            -1 if the container failed to start
            1-255 if the container crashed (it is the return value of the main command of the batch job)
        :param stdout: stdout of the job
        :param stderr: stderr of the job
        :param file: tgz file (as a bytestring) of the content of the batch job container after completion, or None if an error occurred
        """
        self.job_id = job_id
        self.retval = retval
        self.stdout = stdout
        self.stderr = stderr
        self.file = file


class AgentJobStarted(metaclass=MessageMeta, msgtype="agent_job_started"):
    """
        Indicates to the backend that a job started
        A->B.
    """

    def __init__(self, job_id: BackendJobId):
        """
        :param job_id: the backend-side job_id associated to the job
        """
        self.job_id = job_id


class AgentJobDone(metaclass=MessageMeta, msgtype="agent_job_done"):
    """
        Gives the result of a job.
        A->B.
    """

    def __init__(self, job_id: BackendJobId, result: SPResult, grade: float, problems: Dict[str, SPResult], tests: Dict[str, Any],
                 custom: Dict[str, Any], archive: Optional[bytes], stdout: Optional[str], stderr: Optional[str]):
        """
        :param job_id: the backend-side job id associated with this job
        :param result: a tuple that contains the result itself, either:
            - "killed": the container was killed externally (not really an error)
            - "crash": the container crashed (INGInious error)
            - "overflow": the container was killed due to a memory overflow (student/task writer error)
            - "timeout": the container was killed due to a timeout (student/task writer error)
            - "success": the student succeeded to resolve this task
            - "failed": the student failed to succeed this task
            - "error": an error happenned in the grading script (task writer error)
            and the feedback text.
        :param grade: grade
        :param problems: particular feedbacks for each subproblem. Keys are subproblem ids
        :param tests: tests made in the container
        :param custom: custom values
        :param archive: bytes string containing an archive of the content of the container as a tgz
        :param stdout: container stdout
        :param stderr : container stderr
        """
        self.job_id = job_id
        self.result = result
        self.grade = grade
        self.problems = problems
        self.tests = tests
        self.custom = custom
        self.archive = archive
        self.stdout = stdout
        self.stderr = stderr


class AgentJobSSHDebug(metaclass=MessageMeta, msgtype="agent_job_ssh_debug"):
    """
        Gives the necessary info to SSH into a job running in ssh debug mode
    """

    def __init__(self, job_id: BackendJobId, host: str, port: int, password: str):
        """
        :param job_id: the backend-side job id associated with this job
        :param host: host to which the client should connect
        :param port: port on which sshd is bound
        :param password: password that allows to connect to the container
        """
        self.job_id = job_id
        self.host = host
        self.port = port
        self.password = password


#################################################################
#                                                               #
#                  Killer Watcher Pipeline                      #
#                                                               #
#################################################################

class KWPKilledStatus(metaclass=MessageMeta, msgtype="kwp_killed_status"):
    """
        Ask watchers in the pipeline to fill this message with data about the container.
        Watchers should send the updated message throught the pipeline
    """

    def __init__(self, container_id: str, killed_result: Optional[str] = None):
        """
        :param container_id: container to check
        :param killed_result: result that will be sent to the client (timeout, overflow...) if the container was killed, None if it was None
        """
        self.container_id = container_id
        self.killed_result = killed_result

    def killed(self, reason):
        """
        :return: a new KilledStatus with killed_result=reason
        """
        return KWPKilledStatus(self.container_id, reason)

    def not_killed(self):
        """
        :return: the current KilledStatus
        """
        return self


class KWPRegisterContainer(metaclass=MessageMeta, msgtype="kwp_register_container"):
    """
        Register a container with given limitations
    """

    def __init__(self, container_id: str, max_mem: int, timeout: int, timeout_hard: int):
        """
        :param container_id: container to register
        :param max_mem: max memory allowed for the container, in MB
        :param timeout: timeout in seconds
        :param timeout_hard: hard timeout in seconds
        """
        self.container_id = container_id
        self.max_mem = max_mem
        self.timeout = timeout
        self.timeout_hard = timeout_hard


#################################################################
#                                                               #
#                           Heartbeat                           #
#                                                               #
#################################################################

class Ping(metaclass=MessageMeta, msgtype="ping"):
    """
    Ping message
    """

    def __init__(self):
        pass


class Pong(metaclass=MessageMeta, msgtype="pong"):
    """
    Pong message
    """

    def __init__(self):
        pass


class Unknown(metaclass=MessageMeta, msgtype="unknown"):
    """
    Unknown message. Sent by a server that do not know a specific client; probably because the server restarted
    """

    def __init__(self):
        pass


#################################################################
#                                                               #
#                     Docker event watcher                      #
#                                                               #
#################################################################

class EventContainerDied(metaclass=MessageMeta, msgtype="event_container_died"):
    """
    Message used internally in the Docker Agent to signal that a container has closed
    """

    def __init__(self, container_id: str, retval: int):
        self.container_id = container_id
        self.retval = retval


class EventContainerOOM(metaclass=MessageMeta, msgtype="event_container_oom"):
    """
    Message used internally in the Docker Agent to signal that a container has made an OOM
    """

    def __init__(self, container_id: str):
        self.container_id = container_id
