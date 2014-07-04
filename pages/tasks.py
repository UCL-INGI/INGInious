from modules.base import renderer
from modules.login import loginInstance
from modules.tasks import Task
import web
import modules.job_manager as job_manager
from modules.session import sessionManager
import json

#Task page
class TaskPage:
    #Simply display the page
    def GET(self,courseId,taskId):
        if loginInstance.isLoggedIn():
            #try:#TODO:enable
                task = Task(courseId,taskId)
                return renderer.task(task)
            #except:
            #    return renderer.error404()
        else:
            return renderer.index(False)
    def POST(self,courseId,taskId):
        if loginInstance.isLoggedIn():
            #try:#TODO:enable
                task = Task(courseId,taskId)
                userinput = web.input()
                if "@action" in userinput and userinput["@action"] == "submit":
                    jobId = job_manager.addJob(task, web.input)
                    
                    if "waitingJobs" not in sessionManager.get():
                        sessionManager.get().waitingJobs={}
                    sessionManager.get().waitingJobs[jobId]={"courseId": courseId, "taskId": taskId}
                    return json.dumps({"status":"ok","jobId":jobId});
                elif "@action" in userinput and userinput["@action"] == "check" and "jobId" in userinput:
                    if job_manager.isDone(int(userinput['jobId'])):
                        return json.dumps({"status":"done","result":"error","text":"TODO"});
                    else:
                        return json.dumps({'status':"waiting"});
                else:
                    return renderer.error404()
            #except:
            #    return renderer.error404()
        else:
            return renderer.index(False)