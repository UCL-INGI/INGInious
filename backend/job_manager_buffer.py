""" Contains the JobManagerBuffer, which creates a buffer for a JobManager """


class JobManagerBuffer(object):

    """ A buffer for a JobManager """

    def __init__(self, job_manager):
        self._job_manager = job_manager
        self._waiting_jobs = []
        self._jobs_done = {}

    def new_job(self, task, inputdata):
        """ Runs a new job. It works exactly like the JobManager class, instead that there is no callback """
        jobid = self._job_manager.new_job(task, inputdata, self._callback)
        self._waiting_jobs.append(jobid)
        return jobid

    def _callback(self, jobid, _, result):
        """ Callback for self._job_manager.new_job """
        self._jobs_done[jobid] = result
        self._waiting_jobs.remove(jobid)

    def is_waiting(self, jobid):
        """ Return true if the job is in queue """
        return jobid in self._waiting_jobs

    def is_done(self, jobid):
        """ Return true if the job is done """
        return jobid in self._jobs_done

    def get_result(self, jobid):
        """ Get the result of task. Must only be called ONCE, AFTER the task is done (after a successfull call to is_done). """
        result = self._jobs_done[jobid]
        del self._jobs_done[jobid]
        return result
