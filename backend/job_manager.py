import Queue
import threading

class JobManager (threading.Thread):
    """ Thread Class that runs the jobs that are in the queue """
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            # Monitor lock and check
            condition.acquire()
            if main_queue.empty():
                condition.wait()
            
            # Launch the task
            jobId,task,inputdata = main_queue.get()
            main_dict[jobId] = {"task":task,"result":"Done","input":inputdata}
            
            # Monitor notify
            condition.notify()
            condition.release()

def addJob(task, inputdata):
    """ Add a job in the queue and returns a job id.
        task is a Task instance and inputdata is the input as a dictionary """
    # Monitor lock
    condition.acquire()
    
    # Put task in the job queue
    addJob.cur_id  += 1
    jobId = addJob.cur_id
    main_queue.put((jobId,task,inputdata))
    main_dict[jobId] = None
    
    # Monitor notify
    condition.notify()
    condition.release()
    
    # Returns the jobId
    return jobId

def isRunning(jobId):
    """ Tells if a job given by job id is running/in queue """
    if main_dict.has_key(jobId):
        return main_dict[jobId] == None
    else:
        return False

def isDone(jobId):
    """ Tells if a job given y job id is done and its result is available """
    if main_dict.has_key(jobId):
        return main_dict[jobId] != None
    else:
        return False

def getResult(jobId):
    """ Returns the result of a job given by a job id or None if the job is not finished/in queue. If the job is finished, subsequent call to getResult will return None (job is deleted) """
    result = None
    
    # Delete result from dictionary if there is sth
    if main_dict.has_key(jobId) and (not main_dict[jobId] == None):
        result = main_dict[jobId]
        del main_dict[jobId]
        
    return result

# Initialization
addJob.cur_id = 0 # static variable
condition = threading.Condition()
main_queue = Queue.Queue()
main_dict = {}

# Launch the main thread
main_thread = JobManager()
main_thread.daemon = True
main_thread.start()
