""" Manages submissions """
from datetime import datetime
import base64

from bson.objectid import ObjectId
from sh import git  # pylint: disable=no-name-in-module
import pymongo

from backend.docker_job_manager import DockerJobManager
from backend.simple_job_queue import SimpleJobQueue
from common.base import INGIniousConfiguration
from frontend.base import database, gridfs
from frontend.plugins.plugin_manager import PluginManager
from frontend.user_data import UserData
import frontend.user as User
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

    PluginManager.get_instance().call_hook("submission_done", submission=submission, job=job)


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
