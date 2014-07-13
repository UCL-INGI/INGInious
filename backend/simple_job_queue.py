from backend.job_queue import JobQueueSender, JobQueueReceiver
import Queue
import uuid

class SimpleJobQueue(JobQueueSender,JobQueueReceiver):
    """ A really simple job queue """
    
    def __init__(self):
        self.dict = {}
        self.queue = Queue.Queue()
        
    def addJob(self, task, inputdata, callback = None):
        """ Add a job in the queue and returns a job id.
        task is a Task instance and inputdata is the input as a dictionary
        callback is a function (that can be None) that will be called ASYNC when the job is done. 
        The callback receives the jobId as argument"""

        jobId = uuid.uuid4()
        self.queue.put((jobId,task,inputdata,callback))
        self.dict[jobId] = None
        
        # Returns the jobId
        return jobId
    
    def isRunning(self, jobId):
        """ Tells if a job given by job id is running/in queue """
        if self.dict.has_key(jobId):
            return self.dict[jobId] == None
        else:
            return False
    
    def isDone(self, jobId):
        """ Tells if a job given by its job id is done and its result is available """
        if self.dict.has_key(jobId):
            return self.dict[jobId] != None
        else:
            return False
    
    def getResult(self,jobId):
        """ Returns the result of a job given by a job id or None if the job is not finished/in queue. 
            If the job is finished, subsequent call to getResult will return None (job is deleted) 
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
        if self.dict.has_key(jobId) and (not self.dict[jobId] == None):
            result = self.dict[jobId]
            del self.dict[jobId]
            
        return result
    
    def getNextJob(self):
        """ Returns a job to do. Wait until there is a job. The returned job is now in the "running" state. Must return a tuple containing (jobId,task,inputdata,callback) """
        return self.queue.get()
    
    def setResult(self,jobId,result):
        """ Set the result for a job. After the call to this method, the job is in the "done" state. See the getResult method for the content of result """
        self.dict[jobId] = result