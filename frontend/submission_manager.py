""" Compatibility layer to allow app_frontend to retain some informations about who created a job"""

import backend.job_manager
import frontend.user as User
from frontend.base import database, gridFS
from bson.objectid import ObjectId
import threading
import Queue
from datetime import datetime

def initBackendInterface():
    """ Updates the submissions that have a jobId with the status error, as the server restarted """
    database.submissions.update({'jobId':{"$exists":True}},{"$unset":{'jobId':""},"$set":{'status':'error','text':'Internal error. Server restarted'}})
    pass

def getSubmission(submissionId,userCheck=True):
    s = database.submissions.find_one({'_id': ObjectId(submissionId)})
    if userCheck and not userIsSubmissionOwner(s):
        return None
    return s

def getSubmissionFromJobId(jobId):
    return database.submissions.find_one({'jobId': jobId})

def jobDoneCallback(jobId):
    submission = getSubmissionFromJobId(jobId)
    print submission
    assert submission["status"] == "waiting"
    main_queue.put(submission)
    

def addJob(task, inputdata):
    """ Add a job in the queue and returns a submission id.
        task is a Task instance and inputdata is the input as a dictionary """
    if not User.isLoggedIn():
        raise Exception("A user must be logged in to submit an object")
    
    username = User.getUsername()
    
    jobId = backend.job_manager.addJob(task, inputdata, jobDoneCallback)
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

class JobSaver (threading.Thread):
    """ Thread class that saves results from waiting jobs """
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        while True:
            #try:
                submission = main_queue.get()
                job = backend.job_manager.getResult(submission["jobId"])
                self.save(submission, job)
            #except:
            #    pass
    def save(self,submission,job):
        database.submissions.update(
            {"_id":submission["_id"]},
            {
                "$unset":{"jobId":""},
                "$set":
                {
                    "status": ("done" if job["result"] == "success" or job["result"] == "failed" else "error"), #error only if error was made by pythia
                    "result":job["result"],
                    "text":(job["text"] if "text" in job else None),
                    "problems":(job["problems"] if "problems" in job else {}),
                    "archive":(gridFS.put(job["archive"]) if "archive" in job else None)
                }
            }
        )
        print "TASK CACHE"
        task_cache = database.taskstatus.find_one({"username":submission["username"],"courseId":submission["courseId"],"taskId":submission["taskId"]})
        print task_cache
        if task_cache == None:
            print database.taskstatus.insert({"username":submission["username"],"courseId":submission["courseId"],"taskId":submission["taskId"],"succeeded":(job["result"] == "success")})
        elif not task_cache["succeeded"] and job["result"] == "success":
            print database.taskstatus.save({"_id":task_cache["_id"],"username":submission["username"],"courseId":submission["courseId"],"taskId":submission["taskId"],"succeeded":(job["result"] == "success")})
        print "TASK CACHE END"

main_queue = Queue.Queue()
main_thread = JobSaver()
main_thread.daemon = True
main_thread.start()


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
    