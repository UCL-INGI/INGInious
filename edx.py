""" A simple grader for edx, that stands on the backend of INGInious """

import web
from backend.docker_job_manager import DockerJobManager
from backend.simple_job_queue import SimpleJobQueue
from common.base import INGIniousConfiguration
from common.tasks import Task
import threading
import json
import random

web.config.debug = False

courseId = "edx"
urls = (
    '/grader', 'ManageSubmission',
)

jobQueue = None

def init():
    global jobQueue
    jobQueue = SimpleJobQueue()
    
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
        
class ManageSubmission(object):
    def GET(self):
        return """
        <!DOCTYPE html>
        <html>
            <head>
                <title>EDX test</title>
            </head>
            <body>
                <form action="/" method="post">
                    <textarea style="width:100%; height:400px;" name="xqueue_body">{
    "student_response": "def double(x):\\n return 2*x\\n",
    "grader_payload": "basic"
}</textarea><br/>
                    <input type="submit"/>
                </form>
            </body>
        </html>
"""

    def POST(self):
        web.header('Content-Type', 'application/json')
        postInput = web.input()
        if "xqueue_body" not in postInput:
            return json.dumps({"correct":False,"score":0,"msg":"<p>Internal grader error: no xqueue_body in POST</p>"})
        try:
            edxInput = json.loads(postInput.xqueue_body)
            taskId = edxInput["grader_payload"]
        except:
            return json.dumps({"correct":False,"score":0,"msg":"<p>Internal grader error: cannot decode JSON</p>"})
        
        try:
            task = Task(courseId, taskId)
        except:
            return json.dumps({"correct":False,"score":0,"msg":"<p>Internal grader error: unknown task</p>"})
        
        if not task.inputIsConsistent(edxInput):
            return json.dumps({"correct":False,"score":0,"msg":"<p>Internal grader error: input not consistent with task</p>"})
        
        try:
            jobSemaphore = threading.Semaphore(0)
            def manageOutput(jobId,job):
                print "RETURN JOB"
                manageOutput.jobReturn = job
                jobSemaphore.release()
            global jobQueue
            jobQueue.addJob(task, edxInput, manageOutput)
            jobSemaphore.acquire()
            jobReturn = manageOutput.jobReturn
        except:
            return json.dumps({"correct":False,"score":0,"msg":"<p>Internal grader error: error while grading submission</p>"})
        
        try:
            text = ""
            if "text" in jobReturn:
                text = jobReturn["text"]
            if "problems" in jobReturn:
                for p in jobReturn["problems"]:
                    text += "<br/><h4>"+jobReturn["task"].getProblems()[p].getName()+"</h4>"+jobReturn["problems"][p]
                    
            score = (1 if jobReturn["result"] == "success" else 0)
            if "score" in jobReturn:
                score = jobReturn["score"]
                
            return json.dumps({"correct":(jobReturn["result"] == "success"),"score": score, "msg": text})
        except:
            return json.dumps({"correct":False,"score":0,"msg":"<p>Internal grader error: error converting submission result</p>"})
    

app = web.application(urls, globals())
if __name__ == "__main__":
    init()
    app.run()