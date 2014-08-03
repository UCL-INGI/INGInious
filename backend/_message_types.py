"""
    Contains the message types that can be sent to the pool manager's queue.

    CONTAINER_IMAGE_BUILT
        Indicates that a container image has been built on a remote docker instance
        Tuple should contain:
        (CONTAINER_IMAGE_BUILT, [docker_instance_id, container_name])
    RUN_JOB
        Runs a new job
        (RUN_JOB, [jobid, input_data, task_directory, limits, environment])
    JOB_LAUNCHED
        Indicates that a job is now running on a remote docker instance.
        (JOB_LAUNCHED, [jobid, containerid])
    CONTAINER_DONE
        Indicates that a container has finished in the remote docker instance.
        (CONTAINER_DONE, [docker_instance_id, containerid])
    JOB_RESULT
        Returns the job results
        (JOB_RESULT, [jobid, results])
    CLOSE
        Closes the pool manager
        (CLOSE, [])
"""
# Message types
CONTAINER_IMAGE_BUILT = 0
RUN_JOB = 1
JOB_LAUNCHED = 2
CONTAINER_DONE = 3
JOB_RESULT = 4
CLOSE = 5