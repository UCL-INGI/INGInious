from frontend.base import database

class UserData:
    """ Allow to get and to modify data stored in database for a particular user
            userdata
            {
                "_id":             "gderval",
                "realname":        "Guillaume Derval",
                "email":           "guillaume.derval@student.uclouvain.be",
                "task_tried":      0,
                "task_succeeded":  0,
                "total_tries":     0,
            }

            user_course
            {
                "username":        "gderval",
                "courseId":        "idCourse1",
                "task_tried":      0,
                "task_succeeded":  0,
                "total_tries":     0
            }

            user_task
            {
                "username":        "gderval",
                "courseId":        "idCourse1",
                "taskId":          "idTask1",
                "tried":           0,
                "succeeded":       False
            }
    """
    
    def __init__(self,username):
        self.username = username
        self.updateCache()
        
    def updateCache(self):
        self.data = database.users.find_and_modify({"_id":self.username},
            {"$setOnInsert":{"realname":"","email":"","task_tried":0,"task_succeeded":0,"total_tries":0}},
            upsert=True,new=True)
        
    def updateBasicInformations(self,realname,email):
        """ Update basic informations in the database """
        database.users.update({"_id":self.username},{"$set":{"realname":realname,"email":email}})
        self.updateCache()
    
    def getCourseData(self,courseId):
        return database.user_courses.find_one({"username":self.username,"courseId":courseId})
    
    def getTaskData(self,courseId,taskId):
        return database.user_tasks.find_one({"username":self.username,"courseId":courseId,"taskId":taskId})
    
    def viewTask(self,task):
        # Insert a new entry if no one exists
        database.user_tasks.update(
            {"username":self.username,"courseId":task.getCourseId(),"taskId":task.getId()},
            {"$setOnInsert":{"username":self.username,"courseId":task.getCourseId(),"taskId":task.getId(),"tried":0,"succeeded":False}},
            upsert=True)
    
    def updateStatsWithNewSubmissionResult(self,submission,job):
        #### Tasks
        # Insert a new entry if no one exists
        obj = database.user_tasks.find_and_modify(
            {"username":self.username,"courseId":submission["courseId"],"taskId":submission["taskId"]},
            {"$setOnInsert":{"username":self.username,"courseId":submission["courseId"],"taskId":submission["taskId"],"tried":0,"succeeded":False}},
            upsert=True)
        newTry = obj == None or obj["tried"] == 0
        
        # Update inc counter
        database.user_tasks.update({"username":self.username,"courseId":submission["courseId"],"taskId":submission["taskId"]},{"$inc":{"tried":1}})
        
        # Set to succeeded if not succeeded yet
        newSucceed = False
        if job["result"] == "success":
            obj = database.user_tasks.find_and_modify({"username":self.username,"courseId":submission["courseId"],"taskId":submission["taskId"],"succeeded":False},{"$set":{"succeeded":True}})
            newSucceed = obj != None and obj["succeeded"] == False
        
        #### Courses
        # Insert a new entry if no one exists
        database.user_courses.update(
            {"username":self.username,"courseId":submission["courseId"]},
            {"$setOnInsert":{"username":self.username,"courseId":submission["courseId"],"task_tried":0,"task_succeeded":0,"total_tries":0}},
            upsert=True)
        
        # Update counters
        database.user_courses.update(
            {"username":self.username,"courseId":submission["courseId"]},
            {"$inc":{"total_tries":1,"task_tried":(1 if newTry else 0),"task_succeeded":(1 if newSucceed else 0)}})
        
        #### User
        database.users.update(
            {"_id":self.username},
            {"$inc":{"total_tries":1,"task_tried":(1 if newTry else 0),"task_succeeded":(1 if newSucceed else 0)}})
        
        self.updateCache()
    