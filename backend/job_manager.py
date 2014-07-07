import Queue
import threading
import socket
import json
import abc

class JobManager (threading.Thread):
    """ Abstract thread class that runs the jobs that are in the queue """
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            # Monitor lock and check
            condition.acquire()
            if main_queue.empty():
                condition.wait()
            
            # Launch the task and save its result in the dictionary
            jobId,task,inputdata = main_queue.get()
            main_dict[jobId] = self.runJob(jobId, task, inputdata)
            
            # Monitor notify
            condition.notify()
            condition.release()
    @abc.abstractmethod
    def runJob(self, jobId, task, inputdata):
        pass

class PythiaJobManager (JobManager):
    def __init__(self):
        JobManager.__init__(self)
    def connect(self):
        self.host="127.0.0.1"
        self.port=9000
        self.sock = socket.create_connection((self.host,self.port))
    def close(self):
        self.sock.close()
    def runJob(self, jobId, task, inputdata):
        self.connect()
        
        # Send message to Pythia
        msg='{ "message":"launch", "id": "'+ str(jobId) +'", "task": ' + task.getJSON() + ', "input": ' + json.dumps(json.dumps(inputdata) + '\n') + ' }'
        self.sock.sendall(msg.encode('utf-8'))
        
        # Read message from Pythia
        rdata = self.sock.recv(1024)
        result = rdata
        while not rdata.endswith('\n'):
            rdata = self.sock.recv(1024)
            result = result + rdata
        self.close()
        
        # Parsing result
        retdict ={"task":task,"input":inputdata}
        result_json = json.loads(result)
    
        if('output' in result_json):
            output_json = json.loads(result_json['output'])
            retdict.update(output_json)
            
        if(result_json['status'] != "success"):
            retdict['result'] = result_json['status']
        
        return retdict

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
main_thread = PythiaJobManager()
main_thread.daemon = True
main_thread.start()
