import Queue
import threading
import json
import abc
import docker
import os.path
from common.base import INGIniousConfiguration

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
                try:
                    emul_result = self.runJob(jobId, task, {"limits": task.getLimits(), "input": inputdata})
                    print json.dumps(emul_result, sort_keys=True, indent=4, separators=(',', ': '))
                except Exception as inst:
                    emul_result = {"result":"error","text":"The grader did not gave any output. This can be because you used too much memory."}
                
                if finaldict['result'] not in ["error","failed","success","timeout","overflow"]:
                    finaldict['result'] = "error"
                    
                if emul_result["result"] not in ["error","timeout","overflow"]:
                    # Merge results
                    novmDict = finaldict
                    finaldict = emul_result
                    
                    finaldict["result"] = "success" if novmDict["result"] == "success" and finaldict["result"] == "success" else "failed"
                    if "text" in finaldict and "text" in novmDict:
                        finaldict["text"] = finaldict["text"]+"\n"+"\n".join(novmDict["text"])
                    elif "text" not in finaldict and "text" in novmDict:
                        finaldict["text"] = "\n".join(novmDict["text"])
                    
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
            

            main_dict[jobId] = finaldict
            if callback != None:
                callback(jobId)
    @abc.abstractmethod
    def runJob(self, jobId, task, inputdata):
        pass

class DockerJobManager (JobManager):
    def __init__(self):
        JobManager.__init__(self)
        self.docker = docker.Client(base_url=INGIniousConfiguration["dockerServerUrl"])
        self.buildAllContainers()
    def buildAllContainers(self):
        """ Ensures all containers are up to date """
        print "- Building containers"
        containers = [ f for f in os.listdir(INGIniousConfiguration["containersDirectory"]) if os.path.isdir(os.path.join(INGIniousConfiguration["containersDirectory"], f)) and os.path.isfile(os.path.join(INGIniousConfiguration["containersDirectory"], f, "Dockerfile"))]
        for container in containers:
            print "\tbuilding "+container
            try:
                self.buildContainer(container)
            except Exception as inst:
                print "\tthere was an error while building the container:"
                print "\t\t"+str(inst)
        print "- Containers have been built"
    def buildContainer(self,container):
        """ Ensures a container is up to date """
        r=self.docker.build(path=os.path.join(INGIniousConfiguration["containersDirectory"],container),tag=INGIniousConfiguration["containerPrefix"]+container,rm=True)
        for i in r:
            if i == "\n" or i == "\r\n":
                continue
            try:
                j = json.loads(i)
            except:
                raise Exception("Error while building "+container+": can't read Docker output")
            if 'error' in j:
                raise Exception("Error while building "+container+": Docker returned error"+j["error"])

    def getSockets(self,containerId):
        """ Utility function to get stdin of a container """
        return self.docker.attach_socket(containerId,{'stdin': 1, 'stream': 1})
    
    def runJob(self, jobId, task, inputdata):
        """ Runs the job by launching a container """
        #limits: currently we only supports time and memory limits. 
        #Memory is the memory used by the VM, in megabytes, and time is the time taken by the script (not the VM!) in seconds
        memLimit = task.getLimits()["memory"]
        if memLimit < 20:
            memLimit = 20
        elif memLimit > 500:
            memLimit = 500
        
        response = self.docker.create_container(
            INGIniousConfiguration["containerPrefix"]+task.getEnvironment(), 
            stdin_open=True, 
            network_disabled=True, 
            volumes={'/ro/task':{}},
            mem_limit=memLimit*1024*1024
        )
        containerId = response["Id"]
        self.docker.start(containerId, binds={os.path.abspath(os.path.join(INGIniousConfiguration["tasksDirectory"],task.getCourseId(),task.getId())):{'ro':True,'bind':'/ro/task'}})
        self.getSockets(containerId).send(json.dumps(inputdata)+"\n")
        self.docker.wait(containerId)
        stdout = str(self.docker.logs(containerId, stdout=True, stderr=False))
        stderr = str(self.docker.logs(containerId, stdout=False, stderr=True))
        return json.loads(stdout)

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
    if main_dict.has_key(jobId) and (not main_dict[jobId] == None):
        result = main_dict[jobId]
        del main_dict[jobId]
        
    return result

# Initialization
addJob.cur_id = 0 # static variable
main_queue = Queue.Queue()
main_dict = {}

# Launch the main thread
main_thread = DockerJobManager()
main_thread.daemon = True
main_thread.start()
