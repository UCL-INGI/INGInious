import web

from common.courses import Course
from frontend.base import renderer
import frontend.user as User
from frontend.base import database
import json
from common.tasks import Task
from os import listdir
from os.path import isfile, join, splitext

# Course administration page
class AdminCoursePage:
    # Simply display the page
    def GET(self, courseId):
        if User.isLoggedIn():
            #try:
                course = Course(courseId)
                if User.getUsername() not in course.getAdmins():
                    raise web.notfound()
                
                output = self.compute(course)
                print json.dumps(output,sort_keys=True, indent=4, separators=(',', ': '))
                return renderer.admin_course(course,output)
            #except:
            #    raise web.notfound()
        else:
            return renderer.index(False)
    
    #Compute everything that is needed:
    def compute(self,course):
        output={"students":{},"tasks":{},"taskErrors":{}}
        #Get all students
        students = list(database.submissions.distinct("username"))
        for student in students:
            #Init the output
            data = database.usercache.find_one({"_id":student})
            name = None
            email = None
            if data != None and "realname" in data and "email" in data:
                name = data['realname']
                email = data['email']
                
            output["students"][student] = {
                "task_done":0, #out:done
                "task_tried":0, #out:done
                "total_tries":0, #out:done
                "tasks":{}, #out:done
                "name":name,
                "email":email,
            }
        #Get all tasks
        tasks = course.getTasks()
        for taskId in tasks:
            #Init the output
            for student in students:
                output["students"][student]["tasks"][taskId] = {
                    "status":"notattempted", #out:done
                    "name":tasks[taskId].getName(),
                    "submissions":[] #out:done
                }
            output["tasks"][taskId]= {
                "student_attempted":0, #out:done
                "student_succeeded":0, #out:done
                "name":tasks[taskId].getName(),
                "submissions":[]
            }
        
        
        #Get all submissions for this course, and parse everything!
        submissions = database.submissions.find({"courseId":course.getId(),"status":{"$in":["done","error"]}})
        for submission in submissions:
            #if submission["status"] != "done" and submission["status"] != "error":
            #    continue
            taskId = submission["taskId"]
            status = "failed"
            if "result" in submission and submission["result"] == "success":
                status = "succeeded"
            student = submission["username"]
            
            output["students"][student]["total_tries"] = output["students"][student]["total_tries"]+1
            if output["students"][student]["tasks"][taskId]["status"] == "notattempted":
                output["students"][student]["task_tried"] = output["students"][student]["task_tried"]+1
                output["tasks"][taskId]["student_attempted"] = output["tasks"][taskId]["student_attempted"]+1
            if status == "succeeded":
                if output["students"][student]["tasks"][taskId]["status"] != "succeeded":
                    output["tasks"][taskId]["student_succeeded"] = output["tasks"][taskId]["student_succeeded"]+1
                    output["students"][student]["task_done"] = output["students"][student]["task_done"]+1
                output["students"][student]["tasks"][taskId]["status"] = status
            elif output["students"][student]["tasks"][taskId]["status"] != "succeeded":
                output["students"][student]["tasks"][taskId]["status"] = status
            submissionSummary = {"id":str(submission["_id"]),"status":status,"submittedOn":submission["submittedOn"].strftime("%d/%m/%Y %H:%M:%S")}
            output["students"][student]["tasks"][taskId]["submissions"].append(submissionSummary)
            output["tasks"][taskId]["submissions"].append(submissionSummary)
            
        #Check if there are errors when loading some tasks
        files = [ splitext(f)[0] for f in listdir(course.getCourseTasksDirectory()) if isfile(join(course.getCourseTasksDirectory(), f)) and splitext(join(course.getCourseTasksDirectory(), f))[1] == ".task"]
        for task in files:
            try:
                Task(course.getId(), task)
            except Exception as inst:
                output[task] = str(inst)
        return output