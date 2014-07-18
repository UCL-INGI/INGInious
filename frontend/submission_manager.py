""" Manages submissions """
from datetime import datetime
import Queue
import StringIO
import base64
import json
import os.path
import shutil
import tarfile
import threading

from bson.objectid import ObjectId
from sh import git  # pylint: disable=no-name-in-module
import pymongo

from backend.docker_job_manager import DockerJobManager
from backend.simple_job_queue import SimpleJobQueue
from common.base import INGIniousConfiguration
from frontend.base import database, gridfs
from frontend.user_data import UserData
import frontend.user as User
submission_git_saver = None
job_queue = None
job_managers = []


def init_backend_interface():
    """ inits everything that makes the backend working """

    # Ensures some indexes
    database.submissions.ensure_index([("username", pymongo.ASCENDING)])
    database.submissions.ensure_index([("courseid", pymongo.ASCENDING)])
    database.submissions.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
    database.submissions.ensure_index([("submitted_on", pymongo.DESCENDING)])  # sort speed

    database.user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)], unique=True)
    database.user_tasks.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING)])
    database.user_tasks.ensure_index([("courseid", pymongo.ASCENDING), ("taskid", pymongo.ASCENDING)])
    database.user_tasks.ensure_index([("courseid", pymongo.ASCENDING)])
    database.user_tasks.ensure_index([("username", pymongo.ASCENDING)])

    database.user_courses.ensure_index([("username", pymongo.ASCENDING), ("courseid", pymongo.ASCENDING)], unique=True)
    database.user_courses.ensure_index([("courseid", pymongo.ASCENDING)])
    database.user_courses.ensure_index([("username", pymongo.ASCENDING)])
    # Updates the submissions that have a jobid with the status error, as the server restarted """
    database.submissions.update({'jobid': {"$exists": True}}, {"$unset": {'jobid': ""}, "$set": {'status': 'error', 'text': 'Internal error. Server restarted'}})

    # Launch the thread that saves submissions to the git repo
    if INGIniousConfiguration["enable_submission_repo"]:
        global submission_git_saver
        submission_git_saver = SubmissionGitSaver()
        submission_git_saver.daemon = True
        submission_git_saver.start()

    # Create the job queue
    global job_queue
    job_queue = SimpleJobQueue()

    # Launch the job managers
    try:
        job_manager_count = int(INGIniousConfiguration.get("job_managers", 1))
    except ValueError:
        print "Configuration entry 'job_managers' must be an integer"
        job_manager_count = 1
    if job_manager_count < 1:
        print "Configuration entry 'job_managers' must be greater than 1"
    for i in range(0, job_manager_count):
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
        job_managers.append(thread)


def get_submission(submissionid, user_check=True):
    """ Get a submission from the database """
    sub = database.submissions.find_one({'_id': ObjectId(submissionid)})
    if user_check and not user_is_submission_owner(sub):
        return None
    return sub


def get_submission_from_jobid(jobid):
    """ Get a waiting submission from its jobid """
    return database.submissions.find_one({'jobid': jobid})


def job_done_callback(jobid, job):
    """ Callback called by JobManager when a job is done. Updates the submission in the database with the data returned after the completion of the job """
    submission = get_submission_from_jobid(jobid)

    # Save submission to database
    database.submissions.update(
        {"_id": submission["_id"]},
        {
            "$unset": {"jobid": ""},
            "$set":
            {
                "status": ("done" if job["result"] == "success" or job["result"] == "failed" else "error"),  # error only if error was made by INGInious
                "result": job["result"],
                "text": (job["text"] if "text" in job else None),
                "problems": (job["problems"] if "problems" in job else {}),
                "archive": (gridfs.put(base64.b64decode(job["archive"])) if "archive" in job else None)
            }
        }
    )
    UserData(submission["username"]).update_stats(submission, job)

    if submission_git_saver is not None:
        submission_git_saver.add((submission, job))


def add_job(task, inputdata):
    """ Add a job in the queue and returns a submission id.
        task is a Task instance and inputdata is the input as a dictionary """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to submit an object")

    username = User.get_username()

    jobid = job_queue.add_job(task, inputdata, job_done_callback)
    obj = {"username": username, "courseid": task.get_course_id(), "taskid": task.get_id(), "input": inputdata, "status": "waiting", "jobid": jobid, "submitted_on": datetime.now()}
    submissionid = database.submissions.insert(obj)
    return submissionid


def is_running(submissionid, user_check=True):
    """ Tells if a submission is running/in queue """
    submission = get_submission(submissionid, user_check)
    return submission["status"] == "waiting"


def is_done(submissionid, user_check=True):
    """ Tells if a submission is done and its result is available """
    submission = get_submission(submissionid, user_check)
    return submission["status"] == "done" or submission["status"] == "error"


def user_is_submission_owner(submission):
    """ Returns true if the current user is the owner of this jobid, false else """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to verify if he owns a jobid")
    return submission["username"] == User.get_username()


class SubmissionGitSaver(threading.Thread):

    """
        Thread class that saves results from submission in the git repo.
        It must be a thread as a git commit can take some time and because we extract archives returned by Job Manager.
        But it must also be launched only one time as our git operations are not really process/tread-safe ;-)
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = Queue.Queue()
        mustdoinit = False
        self.repopath = INGIniousConfiguration["submission_repo_directory"]
        if not os.path.exists(self.repopath):
            mustdoinit = True
            os.mkdir(self.repopath)
        self.git = git.bake('--work-tree=' + self.repopath, '--git-dir=' + os.path.join(self.repopath, '.git'))
        if mustdoinit:
            self.git.init()

    def add(self, submissionid):
        """ Add a new submission to the repo (add the to queue, will be saved async)"""
        self.queue.put(submissionid)

    def run(self):
        while True:
            # try:
            submission, job = self.queue.get()
            self.save(submission, job)
            # except Exception as inst:
            #    print "Exception in JobSaver: "+str(inst)
            #    pass

    def save(self, submission, job):
        """ saves a new submission in the repo (done async) """
        # Save submission to repo
        print "Save submission " + str(submission["_id"]) + " to git repo"
        # Verify that the directory for the course exists
        if not os.path.exists(os.path.join(self.repopath, submission["courseid"])):
            os.mkdir(os.path.join(self.repopath, submission["courseid"]))
        # Idem with the task
        if not os.path.exists(os.path.join(self.repopath, submission["courseid"], submission["taskid"])):
            os.mkdir(os.path.join(self.repopath, submission["courseid"], submission["taskid"]))
        # Idem with the username, but empty it
        dirname = os.path.join(self.repopath, submission["courseid"], submission["taskid"], submission["username"])
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)
        # Now we can put the input, the output and the zip
        open(os.path.join(dirname, 'submitted_on'), "w+").write(str(submission["submitted_on"]))
        open(os.path.join(dirname, 'input.json'), "w+").write(json.dumps(submission["input"]))
        result_obj = {
            "result": job["result"],
            "text": (job["text"] if "text" in job else None),
            "problems": (job["problems"] if "problems" in job else {})
        }
        open(os.path.join(dirname, 'result.json'), "w+").write(json.dumps(result_obj))
        if "archive" in job:
            os.mkdir(os.path.join(dirname, 'output'))
            tar = tarfile.open(mode='r:gz', fileobj=StringIO.StringIO(base64.b64decode(job["archive"])))
            tar.extractall(os.path.join(dirname, 'output'))
            tar.close()

        self.git.add('--all', '.')
        title = " - ".join([str(submission["courseid"]) + "/" + str(submission["taskid"]),
                            str(submission["_id"]),
                            submission["username"],
                            ("success" if "result" in job and job["result"] == "success" else "failed")])
        self.git.commit('-m', title)


def get_user_submissions(task):
    """ Get all the user's submissions for a given task """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to get his submissions")
    cursor = database.submissions.find({"username": User.get_username(), "taskid": task.get_id(), "courseid": task.get_course_id()})
    cursor.sort([("submitted_on", -1)])
    return list(cursor)


def get_user_last_submissions(query, limit):
    """ Get last submissions of a user """
    if not User.is_logged_in():
        raise Exception("A user must be logged in to get his submissions")
    request = query.copy()
    request.update({"username": User.get_username()})
    cursor = database.submissions.find(request)
    cursor.sort([("submitted_on", -1)]).limit(limit)
    return list(cursor)
