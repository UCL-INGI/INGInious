""" A simple job queue """
import Queue
import uuid

from backend.job_queue import JobQueueSender, JobQueueReceiver


class SimpleJobQueue(JobQueueSender, JobQueueReceiver):

    """ A really simple job queue """

    def __init__(self):
        self.dict = {}
        self.queue = Queue.Queue()

    def add_job(self, task, inputdata, callback=None):
        """ Add a job in the queue and returns a job id.
        task is a Task instance and inputdata is the input as a dictionary
        callback is a function (that can be None) that will be called ASYNC when the job is done.
        The callback receives the jobid as argument"""

        jobid = uuid.uuid4()
        self.queue.put((jobid, task, inputdata, callback))
        self.dict[jobid] = None

        # Returns the jobid
        return jobid

    def is_running(self, jobid):
        """ Tells if a job given by job id is running/in queue """
        if jobid in self.dict:
            return self.dict[jobid] is None
        else:
            return False

    def is_done(self, jobid):
        """ Tells if a job given by its job id is done and its result is available """
        if jobid in self.dict:
            return self.dict[jobid] is not None
        else:
            return False

    def get_result(self, jobid):
        """ Returns the result of a job given by a job id or None if the job is not finished/in queue.
            If the job is finished, subsequent call to get_result will return None (job is deleted)
            Results are dictionnaries with content similar to:
            {
                "task":task, #mandatory
                "input":inputdata,#mandatory
                "result": "error", #mandatory
                "text": "Error message to be displayed on the top of the exercice",
                "problems":{"pb1":"Error message for pb1"},
                "archive":"archive in base 64"
            }

            available result type are
            * error: VM crashed
            * failed: student made an error in his answers
            * success: student solved the exercice
            * timeout: student's code has timeout
            * overflow: memory or disk overflow
        """
        result = None

        # Delete result from dictionary if there is sth
        if jobid in self.dict and (not self.dict[jobid] is None):
            result = self.dict[jobid]
            del self.dict[jobid]

        return result

    def get_next_job(self):
        """ Returns a job to do. Wait until there is a job. The returned job is now in the "running" state. Must return a tuple containing (jobid,task,inputdata,callback) """
        return self.queue.get()

    def set_result(self, jobid, result):
        """ Set the result for a job. After the call to this method, the job is in the "done" state. See the get_result method for the content of result """
        self.dict[jobid] = result
