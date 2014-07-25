""" Pages only accessible to the course's admins """
from collections import OrderedDict
from os import listdir
from os.path import isfile, join, splitext
import StringIO
import cStringIO
import codecs
import csv
import json
import tarfile
import tempfile
import time

from bson import json_util
from bson.objectid import ObjectId
import pymongo
import web

from frontend.base import get_database, get_gridfs
from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
import frontend.user as User


class UnicodeWriter(object):

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
        """ Writes a row to the CSV file """
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
        """ Writes multiple rows to the CSV file """
        for row in rows:
            self.writerow(row)


def make_csv(data):
    """ Returns the content of a CSV file with the data of the dict/list data """
    columns = set()
    output = [[]]
    if isinstance(data, dict):
        output[0].append("id")
        for entry in data:
            for col in data[entry]:
                columns.add(col)
    else:
        for entry in data:
            for col in entry:
                columns.add(col)

    for col in columns:
        output[0].append(col)

    if isinstance(data, dict):
        for entry in data:
            new_output = [str(entry)]
            for col in columns:
                new_output.append(unicode(data[entry][col]) if col in data[entry] else "")
            output.append(new_output)
    else:
        for entry in data:
            new_output = []
            for col in columns:
                new_output.append(unicode(entry[col]) if col in entry else "")
            output.append(new_output)

    csv_string = StringIO.StringIO()
    csv_writer = UnicodeWriter(csv_string)
    for row in output:
        csv_writer.writerow(row)
    csv_string.seek(0)
    web.header('Content-Type', 'text/csv; charset=utf-8')
    web.header('Content-disposition', 'attachment; filename=export.csv')
    return csv_string.read()


class AdminCourseStudentListPage(object):

    """ Course administration page """

    def GET(self, courseid):
        """ GET request """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if User.get_username() not in course.get_admins():
                    raise web.notfound()

                user_input = web.input()
                if "dl" in user_input:
                    include_old_submissions = "include_all" in user_input

                    if user_input['dl'] == 'submission':
                        return self.download_submission(user_input['id'], include_old_submissions)
                    elif user_input['dl'] == 'student_task':
                        return self.download_student_task(course, user_input['username'], user_input['task'], include_old_submissions)
                    elif user_input['dl'] == 'student':
                        return self.download_student(course, user_input['username'], include_old_submissions)
                    elif user_input['dl'] == 'course':
                        return self.download_course(course, include_old_submissions)
                    elif user_input['dl'] == 'task':
                        return self.download_task(course, user_input['task'], include_old_submissions)
                return self.page(course)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def submission_url_generator(self, course, username):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "?dl=student&username=" + username

    def page(self, course):
        """ Get all data and display the page """
        data = list(get_database().user_courses.find({"courseid": course.get_id()}))
        data = [dict(f.items() + [("url", self.submission_url_generator(course, f["username"]))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)
        return renderer.admin_course_student_list(course, data)

    def download_submission_set(self, submissions, filename, sub_folders):
        """ Create a tar archive with all the submissions """
        if len(submissions) == 0:
            return renderer.admin_course_not_any_submission()

        try:
            tmpfile = tempfile.TemporaryFile()
            tar = tarfile.open(fileobj=tmpfile, mode='w:')

            for submission in submissions:
                submission_json = StringIO.StringIO(json.dumps(submission, default=json_util.default, indent=4, separators=(',', ': ')))
                submission_json_fname = str(submission["_id"]) + '.json'
                # Generate file info
                for sub_folder in sub_folders:
                    if sub_folder == 'taskid':
                        submission_json_fname = submission['taskid'] + '/' + submission_json_fname
                    elif sub_folder == 'username':
                        submission_json_fname = submission['username'] + '/' + submission_json_fname
                info = tarfile.TarInfo(name=submission_json_fname)
                info.size = submission_json.len
                info.mtime = time.mktime(submission["submitted_on"].timetuple())

                # Add file in tar archive
                tar.addfile(info, fileobj=submission_json)

                # If there is an archive, add it too
                if 'archive' in submission and submission['archive'] is not None and submission['archive'] != "":
                    subfile = get_gridfs().get(submission['archive'])
                    taskfname = str(submission["_id"]) + '.tgz'
                    # Generate file info
                    for sub_folder in sub_folders:
                        if sub_folder == 'taskid':
                            taskfname = submission['taskid'] + '/' + taskfname
                        elif sub_folder == 'username':
                            taskfname = submission['username'] + '/' + taskfname

                    info = tarfile.TarInfo(name=taskfname)
                    info.size = subfile.length
                    info.mtime = time.mktime(submission["submitted_on"].timetuple())

                    # Add file in tar archive
                    tar.addfile(info, fileobj=subfile)

            # Close tarfile and put tempfile cursor at 0
            tar.close()
            tmpfile.seek(0)

            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="' + filename + '"', unique=True)
            return tmpfile.read()
        except:
            raise web.notfound()

    def download_course(self, course, include_old_submissions=False):
        """ Download all submissions for a course """
        submissions = list(get_database().submissions.find({"courseid": course.get_id(), "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([course.get_id()]) + '.tgz', ['username', 'taskid'])

    def download_task(self, course, taskid, include_old_submissions=False):
        """ Download all submission for a task """
        submissions = list(get_database().submissions.find({"taskid": taskid, "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([course.get_id(), taskid]) + '.tgz', ['username'])

    def download_student(self, course, username, include_old_submissions=False):
        """ Download all submissions for a user for a given course """
        submissions = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([username, course.get_id()]) + '.tgz', ['taskid'])

    def download_student_task(self, course, username, taskid, include_old_submissions=True):
        """ Download all submissions for a user for given task """
        submissions = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "taskid": taskid, "status": {"$in": ["done", "error"]}}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, '_'.join([username, course.get_id(), taskid]) + '.tgz', [])

    def download_submission(self, subid, include_old_submissions=False):
        """ Download a specific submission """
        submissions = list(get_database().submissions.find({'_id': ObjectId(subid)}))
        if not include_old_submissions:
            submissions = self._keep_last_submission(submissions)
        return self.download_submission_set(submissions, subid + '.tgz', [])

    def _keep_last_submission(self, submissions):
        """ Internal command used to only keep the last valid submission, if any """
        submissions.sort(key=lambda item: item['submitted_on'], reverse=True)
        tasks = {}
        for sub in submissions:
            if sub["taskid"] not in tasks:
                tasks[sub["taskid"]] = {}
            if sub["username"] not in tasks[sub["taskid"]]:
                tasks[sub["taskid"]][sub["username"]] = sub
            elif tasks[sub["taskid"]][sub["username"]].get("result", "") != "success" and sub.get("result", "") == "success":
                tasks[sub["taskid"]][sub["username"]] = sub
        print tasks
        final_subs = []
        for task in tasks.itervalues():
            for sub in task.itervalues():
                final_subs.append(sub)
        return final_subs


class AdminCourseStudentInfoPage(object):

    """ List information about a student """

    def GET(self, courseid, username):
        """ GET request """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if User.get_username() not in course.get_admins():
                    raise web.notfound()

                return self.page(course, username)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def submission_url_generator(self, course, username, taskid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "?dl=student_task&task=" + taskid + "&username=" + username

    def page(self, course, username):
        """ Get all data and display the page """
        data = list(get_database().user_tasks.find({"username": username, "courseid": course.get_id()}))
        tasks = course.get_tasks()
        result = OrderedDict()
        for taskid in tasks:
            result[taskid] = {"name": tasks[taskid].get_name(), "submissions": 0, "status": "notviewed", "url": self.submission_url_generator(course, username, taskid)}
        for taskdata in data:
            if taskdata["taskid"] in result:
                result[taskdata["taskid"]]["submissions"] = taskdata["tried"]
                if taskdata["tried"] == 0:
                    result[taskdata["taskid"]]["status"] = "notattempted"
                elif taskdata["succeeded"]:
                    result[taskdata["taskid"]]["status"] = "succeeded"
                else:
                    result[taskdata["taskid"]]["status"] = "failed"
        if "csv" in web.input():
            return make_csv(result)
        return renderer.admin_course_student(course, username, result)


class AdminCourseStudentTaskPage(object):

    """ List information about a task done by a student """

    def GET(self, courseid, username, taskid):
        """ GET request """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if User.get_username() not in course.get_admins():
                    raise web.notfound()
                task = course.get_task(taskid)

                return self.page(course, username, task)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def submission_url_generator(self, course, submissionid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "?dl=submission&id=" + submissionid

    def page(self, course, username, task):
        """ Get all data and display the page """
        data = list(get_database().submissions.find({"username": username, "courseid": course.get_id(), "taskid": task.get_id()}).sort([("submitted_on", pymongo.DESCENDING)]))
        data = [dict(f.items() + [("url", self.submission_url_generator(course, str(f["_id"])))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)
        return renderer.admin_course_student_task(course, username, task, data)


class AdminCourseTaskListPage(object):

    """ List informations about all tasks """

    def GET(self, courseid):
        """ GET request """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if User.get_username() not in course.get_admins():
                    raise web.notfound()

                return self.page(course)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def submission_url_generator(self, course, taskid):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "?dl=task&task=" + taskid

    def page(self, course):
        """ Get all data and display the page """
        data = get_database().user_tasks.aggregate(
            [
                {
                    "$match": {"courseid": course.get_id()}
                },
                {
                    "$group":
                    {
                        "_id": "$taskid",
                        "viewed": {"$sum": 1},
                        "attempted": {"$sum": {"$cond": [{"$ne": ["$tried", 0]}, 1, 0]}},
                        "attempts":{"$sum": "$tried"},
                        "succeeded": {"$sum": {"$cond": ["$succeeded", 1, 0]}}
                    }
                }
            ])["result"]

        # Load tasks and verify exceptions
        files = [
            splitext(f)[0] for f in listdir(
                course.get_course_tasks_directory()) if isfile(
                join(
                    course.get_course_tasks_directory(),
                    f)) and splitext(
                    join(
                        course.get_course_tasks_directory(),
                        f))[1] == ".task"]
        output = {}
        errors = []
        for task in files:
            try:
                output[task] = course.get_task(task)
            except Exception as inst:
                errors.append({"taskid": task, "error": str(inst)})
        tasks = OrderedDict(sorted(output.items(), key=lambda t: t[1].get_order()))

        # Now load additionnal informations
        result = OrderedDict()
        for taskid in tasks:
            result[taskid] = {"name": tasks[taskid].get_name(), "viewed": 0, "attempted": 0, "attempts": 0, "succeeded": 0, "url": self.submission_url_generator(course, taskid)}
        for entry in data:
            if entry["_id"] in result:
                result[entry["_id"]]["viewed"] = entry["viewed"]
                result[entry["_id"]]["attempted"] = entry["attempted"]
                result[entry["_id"]]["attempts"] = entry["attempts"]
                result[entry["_id"]]["succeeded"] = entry["succeeded"]
        if "csv" in web.input():
            return make_csv(result)
        return renderer.admin_course_task_list(course, result, errors)


class AdminCourseTaskInfoPage(object):

    """ List informations about a task """

    def GET(self, courseid, taskid):
        """ GET request """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if User.get_username() not in course.get_admins():
                    raise web.notfound()
                task = course.get_task(taskid)

                return self.page(course, task)
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def submission_url_generator(self, course, task, task_data):
        """ Generates a submission url """
        return "/admin/" + course.get_id() + "?dl=student_task&username=" + task_data['username'] + "&task=" + task.get_id()

    def page(self, course, task):
        """ Get all data and display the page """
        data = list(get_database().user_tasks.find({"courseid": course.get_id(), "taskid": task.get_id()}))
        data = [dict(f.items() + [("url", self.submission_url_generator(course, task, f))]) for f in data]
        if "csv" in web.input():
            return make_csv(data)
        return renderer.admin_course_task_info(course, task, data)
