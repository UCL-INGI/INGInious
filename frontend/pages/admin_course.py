import web

from common.courses import Course
from frontend.base import renderer
import frontend.user as User
from common.tasks import Task
import pymongo
import csv
import StringIO
import cStringIO
import codecs
from bson.objectid import ObjectId
from frontend.base import database, gridFS
import json
import tarfile
import tempfile
import time
from bson import json_util
from collections import OrderedDict

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
def makeCSV(data):
    columns = set()
    output = [[]]
    if isinstance(data, dict):
        output[0].append("id")
        for d in data:
            for col in data[d]:
                columns.add(col)
    else:
        for d in data:
            for col in d:
                columns.add(col)

    for col in columns:
        output[0].append(col)

    if isinstance(data, dict):
        for d in data:
            no = [str(d)]
            for col in columns:
                no.append(unicode(data[d][col]) if col in data[d] else "")
            output.append(no)
    else:
        for d in data:
            no = []
            for col in columns:
                no.append(unicode(d[col]) if col in d else "")
            output.append(no)

    csvString = StringIO.StringIO()
    csvwriter = UnicodeWriter(csvString)
    for row in output:
        csvwriter.writerow(row)
    csvString.seek(0)
    web.header('Content-Type','text/csv; charset=utf-8')
    web.header('Content-disposition', 'attachment; filename=export.csv')
    return csvString.read()
    
class AdminCourseStudentListPage:
    """ Course administration page """
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
                    elif userInput['dl'] == 'course':
                        return self.downloadCourse(course)
                    elif userInput['dl'] == 'task':
                        return self.downloadTask(course,userInput['task'])
                return self.page(course)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
    
    def page(self, course):
        data = list(database.user_courses.find({"courseId":course.getId()}))
        if "csv" in web.input():
            return makeCSV(data)
        return renderer.admin_course_student_list(course,data)

    def downloadSubmissionSet(self, submissions, filename, subFolders):
        if submissions.count(True) == 0:
            return renderer.admin_course_not_any_submission()
        
        try:
            tmpfile = tempfile.TemporaryFile()
            tar = tarfile.open(fileobj=tmpfile, mode='w:')
            
            for submission in submissions:
                submissionJson = StringIO.StringIO(json.dumps(submission, default=json_util.default, indent=4, separators=(',', ': ')))
                submissionJsonfname = str(submission["_id"])+'.json'
                # Generate file info
                for subFolder in subFolders:
                    if subFolder == 'taskId':
                        submissionJsonfname = submission['taskId'] + '/' + submissionJsonfname
                    elif subFolder == 'username':
                        submissionJsonfname = submission['username'] + '/' + submissionJsonfname
                info = tarfile.TarInfo(name=submissionJsonfname)
                info.size = submissionJson.len
                info.mtime = time.mktime(submission["submittedOn"].timetuple())
                
                # Add file in tar archive
                tar.addfile(info, fileobj=submissionJson)
                
                # If there is an archive, add it too
                if 'archive' in submission and submission['archive'] != None and submission['archive'] != "":
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
                    info.mtime = time.mktime(submission["submittedOn"].timetuple())
                    
                    # Add file in tar archive
                    tar.addfile(info, fileobj=subfile)
            
            # Close tarfile and put tempfile cursor at 0
            tar.close()
            tmpfile.seek(0)
    
            web.header('Content-Type','application/x-gzip', unique=True)
            web.header('Content-Disposition','attachment; filename="' + filename +'"', unique=True)
            return tmpfile.read()
        except:
            raise web.notfound()
    
    def downloadCourse(self, course):
        submissions = database.submissions.find({"courseId":course.getId(),"status":{"$in":["done","error"]}})
        return self.downloadSubmissionSet(submissions, '_'.join([course.getId()]) + '.tgz', ['username', 'taskId'])  
    
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
        submissions = database.submissions.find({'_id': ObjectId(subid)})
        return self.downloadSubmissionSet(submissions, subid + '.tgz', [])
        
class AdminCourseStudentInfoPage:
    """ List information about a student """
    def GET(self, courseId, username):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                if User.getUsername() not in course.getAdmins():
                    raise web.notfound()
                
                return self.page(course, username)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
        
    def page(self, course, username):
        data = list(database.user_tasks.find({"username":username, "courseId":course.getId()}))
        tasks = course.getTasks()
        result = OrderedDict()
        for taskId in tasks:
            result[taskId] = {"name":tasks[taskId].getName(),"submissions":0,"status":"notviewed"}
        for taskData in data:
            if taskData["taskId"] in result:
                result[taskData["taskId"]]["submissions"] = taskData["tried"]
                if taskData["tried"] == 0:
                    result[taskData["taskId"]]["status"] = "notattempted"
                elif taskData["succeeded"]:
                    result[taskData["taskId"]]["status"] = "succeeded"
                else:
                    result[taskData["taskId"]]["status"] = "failed"
        if "csv" in web.input():
            return makeCSV(result)
        return renderer.admin_course_student(course,username,result)
    

class AdminCourseStudentTaskPage:
    """ List information about a task done by a student """
    def GET(self, courseId, username, taskId):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                if User.getUsername() not in course.getAdmins():
                    raise web.notfound()
                task = Task(courseId,taskId)
                
                return self.page(course, username, task)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
        
    def page(self, course, username, task):
        data = list(database.submissions.find({"username":username, "courseId":course.getId(), "taskId":task.getId()}).sort([("submittedOn",pymongo.DESCENDING)]))
        if "csv" in web.input():
            return makeCSV(data)
        return renderer.admin_course_student_task(course,username,task,data)
    
class AdminCourseTaskListPage:
    """ List informations about all tasks """
    def GET(self, courseId):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                if User.getUsername() not in course.getAdmins():
                    raise web.notfound()
                
                return self.page(course)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
        
    def page(self, course):
        data = database.user_tasks.aggregate(
        [
            {
                "$match":{"courseId":course.getId()}
            },
            {
                "$group":
                {
                    "_id":"$taskId",
                    "viewed":{"$sum":1},
                    "tried":{"$sum":"$tried"},
                    "succeeded":{"$sum":{"$cond":["$succeeded",1,0]}}
                }
            }
        ])["result"]
        result = OrderedDict()
        tasks = course.getTasks()
        for taskId in tasks:
            result[taskId] = {"name":tasks[taskId].getName(),"viewed":0, "tried":0, "succeeded":0}
        for d in data:
            if d["_id"] in result:
                result[d["_id"]]["viewed"] = d["viewed"]
                result[d["_id"]]["tried"] = d["tried"]
                result[d["_id"]]["succeeded"] = d["succeeded"]
        if "csv" in web.input():
            return makeCSV(result)
        return renderer.admin_course_task_list(course,result)
        
class AdminCourseTaskInfoPage:
    """ List informations about a task """
    def GET(self, courseId, taskId):
        if User.isLoggedIn():
            try:
                course = Course(courseId)
                if User.getUsername() not in course.getAdmins():
                    raise web.notfound()
                task = Task(courseId, taskId)
                
                return self.page(course, task)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)
        
    def page(self, course, task):
        data = list(database.user_tasks.find({"courseId":course.getId(), "taskId":task.getId()}))
        if "csv" in web.input():
            return makeCSV(data)
        return renderer.admin_course_task_info(course,task,data)
