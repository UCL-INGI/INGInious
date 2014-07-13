from abc import ABCMeta,abstractmethod

class JobQueueReceiver:
    """ Every job queue sent to a job manager should inherit from this abstract class """
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def getNextJob(self):
        """ Returns a job to do. Wait until there is a job. The returned job is now in the "running" state. Must return a tuple containing (jobId,task,inputdata,callback) """
        return None
    
    @abstractmethod
    def setResult(self,jobId,result):
        """ Set the result for a job. After the call to this method, the job is in the "done" state. See the getResult method for the content of result """
        return
    
class JobQueueSender:
    """ Abstract class that lists all the method needed to create a job queue """
    __metaclass__ = ABCMeta

    @abstractmethod
    def addJob(self, task, inputdata, callback = None):
        """ Add a job in the queue and returns a job id.
        task is a Task instance and inputdata is the input as a dictionary
        callback is a function (that can be None) that will be called ASYNC when the job is done. 
        The callback receives the jobId as argument"""
        return 0
    
    @abstractmethod
    def isRunning(self, jobId):
        """ Tells if a job given by job id is running/in queue """
        return False
    
    @abstractmethod
    def isDone(self, jobId):
        """ Tells if a job given by its job id is done and its result is available """
        return False
    
    @abstractmethod
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
        return None