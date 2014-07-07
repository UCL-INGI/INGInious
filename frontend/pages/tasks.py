import json

import web

from common.tasks import Task
from common.tasks_problems import MultipleChoiceProblem
import frontend.backend_interface as job_manager
from frontend.base import renderer
import frontend.user as User


# Task page
class TaskPage:
    # Simply display the page
    def GET(self, courseId, taskId):
        if User.isLoggedIn():
            try:
                task = Task(courseId, taskId)
                return renderer.task(task)
            except:
                raise web.notfound()
        else:
            return renderer.index(False)

    def POST(self, courseId, taskId):
        if User.isLoggedIn():
            try:
                task = Task(courseId, taskId)
                userinput = web.input()
                if "@action" in userinput and userinput["@action"] == "submit":
                    # Reparse user input with array for multiple choices
                    needArray = self.listMultipleMultipleChoices(task)
                    userinput = web.input(**dict.fromkeys(needArray, []))
                    if not task.inputIsConsistent(userinput):
                        web.header('Content-Type', 'application/json')
                        return json.dumps({"status":"error", "text":"Please answer to all the questions. Your responses were not tested."});
                    jobId = job_manager.addJob(task, userinput)
                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status":"ok", "jobId":jobId});
                elif "@action" in userinput and userinput["@action"] == "check" and "jobId" in userinput:
                    if job_manager.isDone(int(userinput['jobId'])):
                        web.header('Content-Type', 'application/json')
                        result = job_manager.getResult(int(userinput['jobId']))
                        
                        # Copy JSON and delete what cannot be dumped
                        to_json = result.copy() # COPY of dict
                        if 'task' in to_json :
                            del to_json['task']
                        if 'input' in to_json:
                            del to_json['input']
                        if 'archive' in to_json:
                            del to_json['archive']
                        to_json['status'] = 'done'
                        
                        return json.dumps(to_json)
                    else:
                        web.header('Content-Type', 'application/json')
                        return json.dumps({'status':"waiting"});
                else:
                    raise web.notfound()
            except:
                raise web.notfound()
        else:
            return renderer.index(False)

    def listMultipleMultipleChoices(self, task):
        """ List problems in task that expect and array as input """
        o = []
        for problem in task.getProblems():
            if isinstance(problem, MultipleChoiceProblem) and problem.allowMultiple():
                o.append(problem.getId())
        return o
