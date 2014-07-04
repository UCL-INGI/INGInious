import Queue
import threading

class JobManager (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
    def run(self):
        while True:
            # Monitor lock and check
            condition.acquire()
            if main_queue.empty():
                condition.wait()
            
            # Launch the task
            task,inputdata = main_queue.get()
            print task
            
            # Monitor notify
            condition.notify()
            condition.release()

def addJob(task, inputdata):
    # Monitor lock
    condition.acquire()
    
    # Put task in the job queue
    main_queue.put((task,inputdata))
    addJob.cur_id  += 1
    jobId = 'job' + `addJob.cur_id`
    main_dict[jobId] = None
    
    # Monitor notify
    condition.notify()
    condition.release()
    
    # Returns the jobId
    return jobId

def isDone(jobId):
    return main_dict[jobId] != None

def getResult(jobId):
    return main_dict[jobId]

# Initialization
addJob.cur_id = 0 # static variable
condition = threading.Condition()
main_queue = Queue.Queue()
main_dict = {}

# Launch the main thread
main_thread = JobManager(1)
main_thread.daemon = True
main_thread.start()
