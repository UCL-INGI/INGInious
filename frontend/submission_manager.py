from backend.simple_job_queue import SimpleJobQueue
from backend.docker_job_manager import DockerJobManager
import frontend.user as User
from frontend.base import database, gridFS
from common.base import INGIniousConfiguration
from bson.objectid import ObjectId
import threading
import Queue
from datetime import datetime
import pymongo
from sh import git
import os.path
import shutil
import json
import StringIO
import tarfile
from user_data import UserData

submissionGitSaver = None
jobQueue = None
jobManagers = []

def initBackendInterface():
    """ inits everything that makes the backend working """
    
    # Ensures some indexes
    database.submissions.ensure_index([ ("username",pymongo.ASCENDING) ])
    database.submissions.ensure_index([ ("courseId",pymongo.ASCENDING) ])
    database.submissions.ensure_index([ ("courseId",pymongo.ASCENDING), ("taskId",pymongo.ASCENDING) ])
    database.submissions.ensure_index([ ("submittedOn",pymongo.DESCENDING) ]) #sort speed
    
    database.user_tasks.ensure_index([("username",pymongo.ASCENDING),("courseId",pymongo.ASCENDING),("taskId",pymongo.ASCENDING)],unique=True)
    database.user_courses.ensure_index([("username",pymongo.ASCENDING),("courseId",pymongo.ASCENDING)],unique=True)
    
    # Updates the submissions that have a jobId with the status error, as the server restarted """
    database.submissions.update({'jobId':{"$exists":True}},{"$unset":{'jobId':""},"$set":{'status':'error','text':'Internal error. Server restarted'}})
    
    # Launch the thread that saves submissions to the git repo
    if INGIniousConfiguration["enableSubmissionRepo"]:
        global submissionGitSaver
        submissionGitSaver = SubmissionGitSaver()
        submissionGitSaver.daemon = True
        submissionGitSaver.start()
        
    # Create the job queue
    global jobQueue
    jobQueue = SimpleJobQueue()    
    
    # Launch the job managers
    try:
        jobManagerCount = int(INGIniousConfiguration["jobManagers"])
    except:
        print "Configuration entry 'jobManagers' must be an integer"
        jobManagerCount = 1
    if jobManagerCount < 1:
        print "Configuration entry 'jobManagers' must be greater than 1"
    for i in range(0, jobManagerCount):
        print "Starting Job Manager #"+str(i)
        thread = DockerJobManager(jobQueue,INGIniousConfiguration["dockerServerUrl"], INGIniousConfiguration["tasksDirectory"], INGIniousConfiguration["containersDirectory"], INGIniousConfiguration["containerPrefix"])
        
        # Build the containers if needed
        if i == 0 and "buildContainersOnStart" in INGIniousConfiguration and INGIniousConfiguration["buildContainersOnStart"]:
            thread.buildAllDockerContainers()
            
        thread.daemon = True
        thread.start()
        jobManagers.append(thread)

def getSubmission(submissionId,userCheck=True):
    s = database.submissions.find_one({'_id': ObjectId(submissionId)})
    if userCheck and not userIsSubmissionOwner(s):
        return None
    return s

def getSubmissionFromJobId(jobId):
    return database.submissions.find_one({'jobId': jobId})

def jobDoneCallback(jobId,job):
    """ Callback called by JobManager when a job is done. Updates the submission in the database with the data returned after the completion of the job """
    submission = getSubmissionFromJobId(jobId)
    
    #Save submission to database
    database.submissions.update(
        {"_id":submission["_id"]},
        {
            "$unset":{"jobId":""},
            "$set":
            {
                "status": ("done" if job["result"] == "success" or job["result"] == "failed" else "error"), #error only if error was made by INGInious
                "result":job["result"],
                "text":(job["text"] if "text" in job else None),
                "problems":(job["problems"] if "problems" in job else {}),
                "archive":(gridFS.put(job["archive"]) if "archive" in job else None)
            }
        }
    )
    UserData(submission["username"]).updateStatsWithNewSubmissionResult(submission,job)
    
    if submissionGitSaver != None:
        submissionGitSaver.add((submission,job))
        
def addJob(task, inputdata):
    """ Add a job in the queue and returns a submission id.
        task is a Task instance and inputdata is the input as a dictionary """
    if not User.isLoggedIn():
        raise Exception("A user must be logged in to submit an object")
    
    username = User.getUsername()
    
    jobId = jobQueue.addJob(task, inputdata, jobDoneCallback)
    obj = {"username":username,"courseId":task.getCourseId(),"taskId":task.getId(),"input":inputdata,"status":"waiting","jobId":jobId,"submittedOn":datetime.now()}
    submissionId = database.submissions.insert(obj)
    return submissionId

def isRunning(submissionId, userCheck = True):
    """ Tells if a submission is running/in queue """
    submission = getSubmission(submissionId, userCheck)
    return submission["status"] == "waiting"
    
def isDone(submissionId, userCheck = True):
    """ Tells if a submission is done and its result is available """
    submission = getSubmission(submissionId, userCheck)
    return submission["status"] == "done" or submission["status"] == "error"
    
def userIsSubmissionOwner(submission):
    """ Returns true if the current user is the owner of this jobId, false else """
    if not User.isLoggedIn():
        raise Exception("A user must be logged in to verify if he owns a jobId")
    return submission["username"] == User.getUsername()

class SubmissionGitSaver (threading.Thread):
    """ 
        Thread class that saves results from submission in the git repo. 
        It must be a thread as a git commit can take some time and because we extract archives returned by Job Manager.
        But it must also be launched only one time as our git operations are not really process/tread-safe ;-)
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = Queue.Queue()
        mustdoinit = False
        self.repopath = INGIniousConfiguration["submissionRepoDirectory"]
        if not os.path.exists(self.repopath):
            mustdoinit = True
            os.mkdir(self.repopath)
        self.git = git.bake('--work-tree='+self.repopath,'--git-dir='+os.path.join(self.repopath,'.git'))
        if mustdoinit:
            self.git.init()
    def add(self,submissionId):
        self.queue.put(submissionId)
    def run(self):
        while True:
            try:
                submission,job = self.queue.get()
                self.save(submission, job)
            except Exception as inst:
                print "Exception in JobSaver: "+str(inst)
                pass
    def save(self,submission,job):
        #Save submission to repo
        print "Save submission "+str(submission["_id"])+" to git repo"
        #Verify that the directory for the course exists
        if not os.path.exists(os.path.join(self.repopath,submission["courseId"])):
            os.mkdir(os.path.join(self.repopath,submission["courseId"]))
        #Idem with the task
        if not os.path.exists(os.path.join(self.repopath,submission["courseId"],submission["taskId"])):
            os.mkdir(os.path.join(self.repopath,submission["courseId"],submission["taskId"]))
        #Idem with the username, but empty it
        dirname = os.path.join(self.repopath,submission["courseId"],submission["taskId"],submission["username"])
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)
        #Now we can put the input, the output and the zip
        open(os.path.join(dirname,'submittedOn'),"w+").write(str(submission["submittedOn"]))
        open(os.path.join(dirname,'input.json'),"w+").write(json.dumps(submission["input"]))
        resultObj = {
                     "result":job["result"],
                     "text":(job["text"] if "text" in job else None),
                     "problems":(job["problems"] if "problems" in job else {})
                    }
        open(os.path.join(dirname,'result.json'),"w+").write(json.dumps(resultObj))
        if "archive" in job:
            os.mkdir(os.path.join(dirname,'output'))
            tar = tarfile.open(mode='w:gz',fileobj=StringIO(job["archive"]))
            tar.extractall(os.path.join(dirname,'output'))
            tar.close()
            
        self.git.add('--all','.')
        self.git.commit('-m',"'Submission "+str(submission["_id"])+"'")
            
def getUserSubmissions(task):
    """ Get all the user's submissions for a given task """
    if not User.isLoggedIn():
        raise Exception("A user must be logged in to get his submissions")
    cursor = database.submissions.find({"username":User.getUsername(),"taskId":task.getId(),"courseId":task.getCourseId()})
    cursor.sort([("submittedOn",-1)])
    return list(cursor)

def getUserLastSubmissions(query,limit):
    if not User.isLoggedIn():
        raise Exception("A user must be logged in to get his submissions")
    request = query.copy()
    request.update({"username":User.getUsername()})
    cursor = database.submissions.find(request)
    cursor.sort([("submittedOn",-1)]).limit(limit)
    return list(cursor)