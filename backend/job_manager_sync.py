""" A synchronized "layer" for JobManager """
import threading


class JobManagerSync(object):

    """ Runs job synchronously """

    def __init__(self, job_manager):
        self._job_manager = job_manager

    def new_job(self, task, inputdata):
        """
            Runs a new job.
            It works exactly like the JobManager class, instead that there is no callback and directly returns result.
        """
        job_semaphore = threading.Semaphore(0)

        def manage_output(dummy1_, dummy2_, job):
            """ Manages the output of this job """
            print "RETURN JOB"
            manage_output.jobReturn = job
            job_semaphore.release()
        self._job_manager.new_job(task, inputdata, manage_output)
        job_semaphore.acquire()
        job_return = manage_output.jobReturn
        return job_return