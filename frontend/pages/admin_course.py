import web

from common.courses import Course
from frontend.base import renderer
import frontend.user as User
from frontend.base import database
from bson.objectid import ObjectId
from frontend.base import database, gridFS
import json
from common.tasks import Task
import os
from os import listdir
from os.path import isfile, join, splitext
import tarfile
import tempfile
import sys
import time

# Course administration page
class AdminCoursePage:
    # Simply display the page
    def GET(self, courseId):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                if User.getUsername() not in course.getAdmins():
                    raise web.notfound()
                
                userInput = web.input();
                if "dl" in userInput:
                    if userInput['dl'] == 'submission':
                        return self.downloadSubmission(userInput['id'])
                    elif userInput['dl'] == 'student_task':
                        return self.downloadStudentTask(course, userInput['username'], userInput['task'])
                    elif userInput['dl'] == 'student':
                        return self.downloadStudent(course, userInput['username'])
                
                output = self.compute(course)
                print json.dumps(output,sort_keys=True, indent=4, separators=(',', ': '))
                return renderer.admin_course(course,output)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
    
    def downloadSubmissionSet(self, submissions, filename, subFolders):
        #try:
            tmpfile = tempfile.TemporaryFile()
            tar = tarfile.open(fileobj=tmpfile, mode='w:')
            
            for submission in submissions:
                if 'archive' not in submission or submission['archive'] == None:
                    continue
                subfile = gridFS.get(submission['archive'])
                
                taskfname = str(submission["_id"])+'.tgz'
                # Generate file info
                for subFolder in subFolders:
                    if subFolder == 'taskId':
                        taskfname = submission['taskId'] + '/' + taskfname
                    elif subFolder == 'username':
                        taskfname = submission['username'] + '/' + taskfname
                    
                info = tarfile.TarInfo(name=taskfname)
                info.size = subfile.length
                info.mtime = time.mktime(subfile.upload_date.timetuple())
                
                # Add file in tar archive
                tar.addfile(info, fileobj=subfile)
            
            # Close tarfile and put tempfile cursor at 0
            tar.close()
            tmpfile.seek(0)
            web.header('Content-Type','application/x-gzip', unique=True)
            web.header('Content-Disposition','attachment; filename="' + filename +'"', unique=True)
            return tmpfile.read()
        #except:
        #    raise web.notfound()
    
    def downloadCourse(self, course, taskId):
        submissions = database.submissions.find({"courseId":course.getId(),"status":{"$in":["done","error"]}})
        return self.downloadSubmissionSet(submissions, '_'.join([course.getId(), taskId]) + '.tgz', ['username', 'taskId'])  
    
    def downloadTask(self, course, taskId):
        submissions = database.submissions.find({"taskId":taskId,"courseId":course.getId(),"status":{"$in":["done","error"]}})
        return self.downloadSubmissionSet(submissions, '_'.join([course.getId(), taskId]) + '.tgz', ['username'])  
    
    def downloadStudent(self, course, username):
        submissions = database.submissions.find({"username":username,"courseId":course.getId(),"status":{"$in":["done","error"]}})
        return self.downloadSubmissionSet(submissions, '_'.join([username,course.getId()]) + '.tgz', ['taskId'])    
    
    def downloadStudentTask(self, course, username, taskId):
        submissions = database.submissions.find({"username":username,"courseId":course.getId(), "taskId":taskId ,"status":{"$in":["done","error"]}})
        return self.downloadSubmissionSet(submissions, '_'.join([username,course.getId(),taskId]) + '.tgz', [])
    
    def downloadSubmission(self, subid):
        try:
            submission = database.submissions.find_one({'_id': ObjectId(subid)})
            web.header('Content-Type','application/x-gzip', unique=True)
            web.header('Content-Disposition','attachment; filename="' + '_'.join([submission["username"],submission["courseId"],submission["taskId"],str(submission["_id"])]) + '.tgz"', unique=True)
            return gridFS.get(submission['archive']).read()
        except:
            raise web.notfound()
        
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
