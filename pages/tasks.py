from modules.base import renderer
from modules.login import loginInstance
from modules.tasks import Task

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