""" A simple grader for edx, that stands on the backend of INGInious """

import json
import threading

import web

from backend.docker_job_manager import DockerJobManager
from backend.simple_job_queue import SimpleJobQueue
from common.base import INGIniousConfiguration
from common.tasks import Task


web.config.debug = False

courseid = "edx"
urls = (
    '/grader', 'ManageSubmission',
)

job_queue = None


def init():
    INGIniousConfiguration.load("./configuration.edx.json")
    global job_queue
    job_queue = SimpleJobQueue()

    try:
        jobManagerCount = int(INGIniousConfiguration["job_managers"])
    except:
        print "Configuration entry 'job_managers' must be an integer"
        jobManagerCount = 1
    if jobManagerCount < 1:
        print "Configuration entry 'job_managers' must be greater than 1"
    for i in range(0, jobManagerCount):
        print "Starting Job Manager #" + str(i)
        thread = DockerJobManager(
            job_queue,
            INGIniousConfiguration["docker_server_url"],
            INGIniousConfiguration["tasks_directory"],
            INGIniousConfiguration["containers_directory"],
            INGIniousConfiguration["container_prefix"])

        # Build the containers if needed
        if i == 0 and "build_containers_on_start" in INGIniousConfiguration and INGIniousConfiguration["build_containers_on_start"]:
            thread.build_all_docker_containers()

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
            return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: no xqueue_body in POST</p>"})
        try:
            edxInput = json.loads(postInput.xqueue_body)
            taskid = edxInput["grader_payload"]
        except:
            return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: cannot decode JSON</p>"})

        try:
            task = Task(courseid, taskid)
        except:
            return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: unknown task</p>"})

        if not task.input_is_consistent(edxInput):
            return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: input not consistent with task</p>"})

        try:
            jobSemaphore = threading.Semaphore(0)

            def manageOutput(_, job):
                print "RETURN JOB"
                manageOutput.jobReturn = job
                jobSemaphore.release()
            job_queue.add_job(task, edxInput, manageOutput)
            jobSemaphore.acquire()
            jobReturn = manageOutput.jobReturn
        except:
            return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: error while grading submission</p>"})

        try:
            text = ""
            if "text" in jobReturn:
                text = jobReturn["text"]
            if "problems" in jobReturn:
                for p in jobReturn["problems"]:
                    text += "<br/><h4>" + jobReturn["task"].get_problems()[p].get_name() + "</h4>" + jobReturn["problems"][p]

            score = (1 if jobReturn["result"] == "success" else 0)
            if "score" in jobReturn:
                score = jobReturn["score"]

            return json.dumps({"correct": (jobReturn["result"] == "success"), "score": score, "msg": text})
        except:
            return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: error converting submission result</p>"})


app = web.application(urls, globals())
if __name__ == "__main__":
    init()
    app.run()
