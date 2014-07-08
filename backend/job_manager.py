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
            # Retrieves the task from the queue
            jobId,task,inputdata,callback = main_queue.get()
            
            # Base dictonnary with output
            basedict = {"task":task,"input":inputdata}
            
            # Check task answer that do not need emulation
            first_result,need_emul,first_text,first_problems = task.checkAnswer(inputdata)
            finaldict = basedict.copy()
            finaldict.update({"result": ("success" if first_result else "failed")})
            if first_text != None:
                finaldict["text"] = first_text
            if first_problems:
                finaldict["problems"] = first_problems
            
            # Launch the emulation
            if need_emul:
                print "STARTING PYTHIA JOB"
                try:
                    emul_result = self.runJob(jobId, task, inputdata)
                except:
                    emul_result = {"result":"error","text":"Internal error: can't connect to backend"}
                
                if finaldict['result'] not in ["error","failed","success","timeout","overflow"]:
                    finaldict['result'] = "error"
                    
                if emul_result["result"] not in ["error","timeout","overflow"]:
                    # Merge results
                    novmDict = finaldict
                    finaldict = emul_result
                    
                    finaldict["result"] = "success" if novmDict["result"] == "success" and finaldict["result"] == "success" else "failed"
                    if "text" in finaldict and "text" in novmDict:
                        finaldict["text"] = finaldict["text"]+"\n"+novmDict["text"]
                    elif "text" not in finaldict and "text" in novmDict:
                        finaldict["text"] = novmDict["text"]
                    
                    if "problems" in finaldict and "problems" in novmDict:
                        for p in novmDict["problems"]:
                            if p in finaldict["problems"]:
                                finaldict["problems"][p] = finaldict["problems"][p] + "\n" + novmDict["problems"][p]
                            else:
                                finaldict["problems"][p] = novmDict["problems"][p]
                    elif "problems" not in finaldict and "problems" in novmDict:
                        finaldict["problems"] = novmDict["problems"]
                elif emul_result["result"] in ["error","timeout","overflow"] and "text" in emul_result:
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":emul_result["text"]})
                elif emul_result["result"] == "error":
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":"An unknown internal error occured"})
                elif emul_result["result"] == "timeout":
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":"Your code took too much time to execute"})
                elif emul_result["result"] == "overflow":
                    finaldict = basedict.copy()
                    finaldict.update({"result":emul_result["result"],"text":"Your code took too much memory or disk"})
                print "END PYTHIA JOB"
            

            main_dict[jobId] = finaldict
            print "CALL JOB CALLBACK"
            if callback != None:
                callback(jobId)
    @abc.abstractmethod
    def runJob(self, jobId, task, inputdata):
        pass

class PythiaJobManager (JobManager):
    def __init__(self):
        JobManager.__init__(self)
    def connect(self):
        self.host="127.0.0.1"
        self.port=9000
        self.sock = socket.create_connection((self.host,self.port),10)
    def close(self):
        self.sock.close()
    def runJob(self, jobId, task, inputdata):
        try:
            self.connect()
        except socket.error, e:
            return {"result": "crash", "text": "Couldn't connect to Pythia"}
        
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
        retdict ={}
        result_json = json.loads(result)
    
        if('output' in result_json):
            try:
                output_json = json.loads(result_json['output'])
            except ValueError, e:
                output_json = {"result": "crash", "text": "Presentation Error"}
            retdict.update(output_json)
            
        if(result_json['status'] != "success"):
            retdict['result'] = result_json['status']
        
        return retdict

def addJob(task, inputdata, callback = None):
    """ Add a job in the queue and returns a job id.
        task is a Task instance and inputdata is the input as a dictionary
        callback is a function (that can be None) that will be called ASYNC when the job is done. 
        The callback receives the jobId as argument"""
        
    # Put task in the job queue
    addJob.cur_id  += 1
    jobId = addJob.cur_id
    main_queue.put((jobId,task,inputdata,callback))
    main_dict[jobId] = None
    
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
    """ Returns the result of a job given by a job id or None if the job is not finished/in queue. 
        If the job is finished, subsequent call to getResult will return None (job is deleted) 
        Results are dictionnaries with content similar to:
        {
            "task":task,
            "input":inputdata, 
            "result": "error", 
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
    if main_dict.has_key(jobId) and (not main_dict[jobId] == None):
        result = main_dict[jobId]
        del main_dict[jobId]
        
    return result

# Initialization
addJob.cur_id = 0 # static variable
main_queue = Queue.Queue()
main_dict = {}

# Launch the main thread
main_thread = PythiaJobManager()
main_thread.daemon = True
main_thread.start()
