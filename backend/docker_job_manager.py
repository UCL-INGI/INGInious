from backend.job_manager import JobManager
import docker
import os
import json
    
class DockerJobManager (JobManager):
    def __init__(self, jobqueue, serverUrl, tasksDirectory, containersDirectory, containerPrefix):
        JobManager.__init__(self, jobqueue)
        self.docker = docker.Client(base_url=serverUrl)
        self.serverUrl = serverUrl
        self.tasksDirectory = tasksDirectory
        self.containerPrefix = containerPrefix
        self.containersDirectory = containersDirectory

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
            self.containerPrefix+task.getEnvironment(), 
            stdin_open=True, 
            network_disabled=True, 
            volumes={'/ro/task':{}},
            mem_limit=memLimit*1024*1024
        )
        containerId = response["Id"]
        self.docker.start(containerId, binds={os.path.abspath(os.path.join(self.tasksDirectory,task.getCourseId(),task.getId())):{'ro':True,'bind':'/ro/task'}})
        self.getSockets(containerId).send(json.dumps(inputdata)+"\n")
        self.docker.wait(containerId)
        # Get the std outputs
        stdout = str(self.docker.logs(containerId, stdout=True, stderr=False))
        stderr = str(self.docker.logs(containerId, stdout=False, stderr=True))
        if stderr != "":
            print "STDERR: "+stderr
        # Delete used containers to avoid using too much disk space
        self.docker.remove_container(containerId, True, False, True)
        return json.loads(stdout)
    
    def buildDockerContainer(self,container):
        """ Ensures a container is up to date """
        r=self.docker.build(path=os.path.join(self.containersDirectory,container),tag=self.containerPrefix+container,rm=True)
        for i in r:
            if i == "\n" or i == "\r\n":
                continue
            try:
                j = json.loads(i)
            except:
                raise Exception("Error while building "+container+": can't read Docker output")
            if 'error' in j:
                raise Exception("Error while building "+container+": Docker returned error"+j["error"])
                
    def buildAllDockerContainers(self):
        """ Ensures all containers are up to date """
        print "- Building containers"
        containers = [ f for f in os.listdir(self.containersDirectory) if os.path.isdir(os.path.join(self.containersDirectory, f)) and os.path.isfile(os.path.join(self.containersDirectory, f, "Dockerfile"))]
        for container in containers:
            print "\tbuilding "+container
            try:
                self.buildDockerContainer(container)
            except Exception as inst:
                print "\tthere was an error while building the container:"
                print "\t\t"+str(inst)
        print "- Containers have been built"