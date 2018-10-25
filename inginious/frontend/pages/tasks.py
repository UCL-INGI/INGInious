# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Task page """
import json
import mimetypes
import posixpath
import urllib.error
import urllib.parse
import urllib.request
import random
import time

import web
from bson.objectid import ObjectId
from collections import OrderedDict

from inginious.common import exceptions
from inginious.frontend.pages.utils import INGIniousPage


class BaseTaskPage(object):
    """ Display a task (and allow to reload old submission/file uploaded during a submission) """

    def __init__(self, calling_page):
        self.cp = calling_page
        self.submission_manager = self.cp.submission_manager
        self.user_manager = self.cp.user_manager
        self.database = self.cp.database
        self.course_factory = self.cp.course_factory
        self.template_helper = self.cp.template_helper
        self.default_allowed_file_extensions = self.cp.default_allowed_file_extensions
        self.default_max_file_size = self.cp.default_max_file_size
        self.webterm_link = self.cp.webterm_link
        self.plugin_manager = self.cp.plugin_manager

    def set_selected_submission(self, course, task, submissionid):
        """ Set submission whose id is `submissionid` to selected grading submission for the given course/task.
            Returns a boolean indicating whether the operation was successful or not.
        """

        submission = self.submission_manager.get_submission(submissionid)

        # Do not continue if submission does not exist or is not owned by current user
        if not submission:
            return False

        # Check if the submission if from this task/course!
        if submission["taskid"] != task.get_id() or submission["courseid"] != course.get_id():
            return False

        is_staff = self.user_manager.has_staff_rights_on_course(course, self.user_manager.session_username())

        # Do not enable submission selection after deadline
        if not task.get_accessible_time().is_open() and not is_staff:
            return False

        # Only allow to set submission if the student must choose their best submission themselves
        if task.get_evaluate() != 'student' and not is_staff:
            return False

        # Check if task is done per group/team
        if task.is_group_task() and not is_staff:
            group = self.database.aggregations.find_one(
                {"courseid": task.get_course_id(), "groups.students": self.user_manager.session_username()},
                {"groups": {"$elemMatch": {"students": self.user_manager.session_username()}}})
            students = group["groups"][0]["students"]
        else:
            students = [self.user_manager.session_username()]

        # Check if group/team is the same
        if students == submission["username"]:
            self.database.user_tasks.update_many(
                {"courseid": task.get_course_id(), "taskid": task.get_id(), "username": {"$in": students}},
                {"$set": {"submissionid": submission['_id'],
                          "grade": submission['grade'],
                          "succeeded": submission["result"] == "success"}})
            return True
        else:
            return False

    def GET(self, courseid, taskid, isLTI):
        """ GET request """
        username = self.user_manager.session_username()

        # Fetch the course
        try:
            course = self.course_factory.get_course(courseid)
        except exceptions.CourseNotFoundException as ex:
            raise web.notfound(str(ex))

        if isLTI and not self.user_manager.course_is_user_registered(course):
            self.user_manager.course_register_user(course, force=True)

        if not self.user_manager.course_is_open_to_user(course, username, isLTI):
            return self.template_helper.get_renderer().course_unavailable()

        # Fetch the task
        try:
            tasks = OrderedDict((tid, t) for tid, t in course.get_tasks().items() if self.user_manager.task_is_visible_by_user(t, username, isLTI))
            task = tasks[taskid]
        except exceptions.TaskNotFoundException as ex:
            raise web.notfound(str(ex))

        if not self.user_manager.task_is_visible_by_user(task, username, isLTI):
            return self.template_helper.get_renderer().task_unavailable()

        # Compute previous and next taskid
        keys = list(tasks.keys())
        index = keys.index(taskid)
        previous_taskid = keys[index - 1] if index > 0 else None
        next_taskid = keys[index + 1] if index < len(keys) - 1 else None

        self.user_manager.user_saw_task(username, courseid, taskid)

        is_staff = self.user_manager.has_staff_rights_on_course(course, username)
        
        # Generate random inputs and save it into db
        random_input_list = []
        random.seed(str(username if username is not None else "") + taskid + courseid + str(time.time() if task.regenerate_input_random() else ""))
        random_input_list = [random.random() for i in range(task.get_number_input_random())]
        if username is not None and len(random_input_list) > 0: # Avoid errors when visitors/unregistered users and avoid pollute db if input random not using
            self.database.user_tasks.update(
                    {"courseid": task.get_course_id(), "taskid": task.get_id(), "username": username},
                    {"$set": {"random": random_input_list}})

        userinput = web.input()
        if "submissionid" in userinput and "questionid" in userinput:
            # Download a previously submitted file
            submission = self.submission_manager.get_submission(userinput["submissionid"], user_check=not is_staff)
            if submission is None:
                raise web.notfound()
            sinput = self.submission_manager.get_input_from_submission(submission, True)
            if userinput["questionid"] not in sinput:
                raise web.notfound()

            if isinstance(sinput[userinput["questionid"]], dict):
                # File uploaded previously
                mimetypes.init()
                mime_type = mimetypes.guess_type(urllib.request.pathname2url(sinput[userinput["questionid"]]['filename']))
                web.header('Content-Type', mime_type[0])
                return sinput[userinput["questionid"]]['value']
            else:
                # Other file, download it as text
                web.header('Content-Type', 'text/plain')
                return sinput[userinput["questionid"]]
        else:
            # user_task always exists as we called user_saw_task before
            user_task = self.database.user_tasks.find_one({
                "courseid": task.get_course_id(),
                "taskid": task.get_id(),
                "username": self.user_manager.session_username()
            })

            submissionid = user_task.get('submissionid', None)
            eval_submission = self.database.submissions.find_one({'_id': ObjectId(submissionid)}) if submissionid else None

            students = [self.user_manager.session_username()]
            if task.is_group_task() and not self.user_manager.has_admin_rights_on_course(course, username):
                group = self.database.aggregations.find_one(
                    {"courseid": task.get_course_id(), "groups.students": self.user_manager.session_username()},
                    {"groups": {"$elemMatch": {"students": self.user_manager.session_username()}}})
                if group is not None and len(group["groups"]) > 0:
                    students = group["groups"][0]["students"]
                # we don't care for the other case, as the student won't be able to submit.

            submissions = self.submission_manager.get_user_submissions(task) if self.user_manager.session_logged_in() else []
            user_info = self.database.users.find_one({"username": username})

            # Display the task itself
            return self.template_helper.get_renderer().task(user_info, course, task, submissions,
                                                            students, eval_submission, user_task, previous_taskid, next_taskid, self.webterm_link, random_input_list)

    def POST(self, courseid, taskid, isLTI):
        """ POST a new submission """
        username = self.user_manager.session_username()
        try:
            course = self.course_factory.get_course(courseid)
            if not self.user_manager.course_is_open_to_user(course, username, isLTI):
                return self.template_helper.get_renderer().course_unavailable()

            task = course.get_task(taskid)
            if not self.user_manager.task_is_visible_by_user(task, username, isLTI):
                return self.template_helper.get_renderer().task_unavailable()

            self.user_manager.user_saw_task(username, courseid, taskid)

            is_staff = self.user_manager.has_staff_rights_on_course(course, username)
            is_admin = self.user_manager.has_admin_rights_on_course(course, username)

            userinput = web.input()
            if "@action" in userinput and userinput["@action"] == "submit":
                # Verify rights
                if not self.user_manager.task_can_user_submit(task, username, isLTI):
                    return json.dumps({"status": "error", "text": _("You are not allowed to submit for this task.")})
                    
                # Retrieve input random and check still valid
                random_input = self.database.user_tasks.find_one({"courseid": task.get_course_id(), "taskid": task.get_id(), "username": username}, { "random": 1 })
                random_input = random_input["random"] if "random" in random_input else []
                for i in range(0, len(random_input)):
                    s = "@random_" + str(i)
                    if s not in userinput or float(userinput[s]) != random_input[i]:
                        return json.dumps({"status": "error", "text": _("Your task has been regenerated. This current task is outdated.")})

                # Reparse user input with array for multiple choices
                init_var = {
                    problem.get_id(): problem.input_type()()
                    for problem in task.get_problems() if problem.input_type() in [dict, list]
                }
                userinput = task.adapt_input_for_backend(web.input(**init_var))

                if not task.input_is_consistent(userinput, self.default_allowed_file_extensions, self.default_max_file_size):
                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "error", "text": _("Please answer to all the questions and verify the extensions of the files "
                                                                  "you want to upload. Your responses were not tested.")})
                del userinput['@action']

                # Get debug info if the current user is an admin
                debug = is_admin
                if "@debug-mode" in userinput:
                    if userinput["@debug-mode"] == "ssh" and debug:
                        debug = "ssh"
                    del userinput['@debug-mode']

                # Start the submission
                try:
                    submissionid, oldsubids = self.submission_manager.add_job(task, userinput, debug)
                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "ok", "submissionid": str(submissionid), "remove": oldsubids, "text": _("<b>Your submission has been sent...</b>")})
                except Exception as ex:
                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "error", "text": str(ex)})

            elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
                result = self.submission_manager.get_submission(userinput['submissionid'], user_check=not is_staff)
                if result is None:
                    web.header('Content-Type', 'application/json')
                    return json.dumps({'status': "error", "text": _("Internal error")})
                elif self.submission_manager.is_done(result, user_check=not is_staff):
                    web.header('Content-Type', 'application/json')
                    result = self.submission_manager.get_input_from_submission(result)
                    result = self.submission_manager.get_feedback_from_submission(result, show_everything=is_staff)

                    # user_task always exists as we called user_saw_task before
                    user_task = self.database.user_tasks.find_one({
                        "courseid":task.get_course_id(),
                        "taskid": task.get_id(),
                        "username": {"$in": result["username"]}
                    })

                    default_submissionid = user_task.get('submissionid', None)
                    if default_submissionid is None:
                        # This should never happen, as user_manager.update_user_stats is called whenever a submission is done.
                        return json.dumps({'status': "error", "text": _("Internal error")})

                    return self.submission_to_json(task, result, is_admin, False, default_submissionid == result['_id'], tags=task.get_tags())
                else:
                    web.header('Content-Type', 'application/json')
                    return self.submission_to_json(task, result, is_admin)

            elif "@action" in userinput and userinput["@action"] == "load_submission_input" and "submissionid" in userinput:
                submission = self.submission_manager.get_submission(userinput["submissionid"], user_check=not is_staff)
                submission = self.submission_manager.get_input_from_submission(submission)
                submission = self.submission_manager.get_feedback_from_submission(submission, show_everything=is_staff)
                if not submission:
                    raise web.notfound()
                web.header('Content-Type', 'application/json')
                
                return self.submission_to_json(task, submission, is_admin, True, tags=task.get_tags())
                
            elif "@action" in userinput and userinput["@action"] == "kill" and "submissionid" in userinput:
                self.submission_manager.kill_running_submission(userinput["submissionid"])  # ignore return value
                web.header('Content-Type', 'application/json')
                return json.dumps({'status': 'done'})
            elif "@action" in userinput and userinput["@action"] == "set_submission" and "submissionid" in userinput:
                web.header('Content-Type', 'application/json')
                if task.get_evaluate() != 'student':
                    return json.dumps({'status': "error"})

                if self.set_selected_submission(course, task, userinput["submissionid"]):
                    return json.dumps({'status': 'done'})
                else:
                    return json.dumps({'status': 'error'})
            else:
                raise web.notfound()
        except:
            if web.config.debug:
                raise
            else:
                raise web.notfound()

    def submission_to_json(self, task, data, debug, reloading=False, replace=False, tags={}):
        """ Converts a submission to json (keeps only needed fields) """

        if "ssh_host" in data:
            return json.dumps({'status': "waiting", 'text': "<b>SSH server active</b>",
                               'ssh_host': data["ssh_host"], 'ssh_port': data["ssh_port"],
                               'ssh_password': data["ssh_password"]})

        # Here we are waiting. Let's send some useful information.
        waiting_data = self.submission_manager.get_job_queue_info(data["jobid"]) if "jobid" in data else None
        if waiting_data is not None and not reloading:
            nb_tasks_before, approx_wait_time = waiting_data
            wait_time = round(approx_wait_time)
            if nb_tasks_before == -1 and wait_time <= 0:
                text = _("<b>INGInious is currently grading your answers.<b/> (almost done)")
            elif nb_tasks_before == -1:
                text = _("<b>INGInious is currently grading your answers.<b/> (Approx. wait time: {} seconds)").format(
                    wait_time)
            elif nb_tasks_before == 0:
                text = _("<b>You are next in the waiting queue!</b>")
            elif nb_tasks_before == 1:
                text = _("<b>There is one task in front of you in the waiting queue.</b>")
            else:
                text = _("<b>There are {} tasks in front of you in the waiting queue.</b>").format(nb_tasks_before)

            return json.dumps({'status': "waiting", 'text': text})

        tojson = {
            'status': data['status'],
            'result': data.get('result', 'crash'),
            'id': str(data["_id"]),
            'submitted_on': str(data['submitted_on']),
            'grade': str(data.get("grade", 0.0)),
            'replace': replace and not reloading  # Replace the evaluated submission
        }

        if "text" in data:
            tojson["text"] = data["text"]
        if "problems" in data:
            tojson["problems"] = data["problems"]

        if debug:
            tojson["debug"] = data

        if tojson['status'] == 'waiting':
            tojson["text"] = _("<b>Your submission has been sent...</b>")
        elif tojson["result"] == "failed":
            tojson["text"] = _("There are some errors in your answer. Your score is {score}%.").format(score=data["grade"])
        elif tojson["result"] == "success":
            tojson["text"] = _("Your answer passed the tests! Your score is {score}%.").format(score=data["grade"])
        elif tojson["result"] == "timeout":
            tojson["text"] = _("Your submission timed out. Your score is {score}%.").format(score=data["grade"])
        elif tojson["result"] == "overflow":
            tojson["text"] = _("Your submission made an overflow. Your score is {score}%.").format(score=data["grade"])
        elif tojson["result"] == "killed":
            tojson["text"] = _("Your submission was killed.")
        else:
            tojson["text"] = _("An internal error occurred. Please retry later. "
                               "If the error persists, send an email to the course administrator.")

        tojson["text"] = "<b>" + tojson["text"] + " " + _("[Submission #{submissionid}]").format(submissionid=data["_id"]) + "</b>" + data.get("text", "")
        tojson["text"] = self.plugin_manager.call_hook_recursive("feedback_text", task=task, submission=data, text=tojson["text"])["text"]

        if reloading:
            # Set status='ok' because we are reloading an old submission.
            tojson["status"] = 'ok'
            # And also include input
            tojson["input"] = data.get('input', {})

        if "tests" in data:
            tojson["tests"] = {}
            if tags:
                for tag in tags[0]+tags[1]: # Tags only visible for admins should not appear in the json for students.
                    if (tag.is_visible_for_student() or debug) and tag.get_id() in data["tests"]:
                        tojson["tests"][tag.get_id()] = data["tests"][tag.get_id()]
            if debug: #We add also auto tags when we are admin
                for tag in data["tests"]:
                    if tag.startswith("*auto-tag-"):
                        tojson["tests"][tag] = data["tests"][tag]

        # allow plugins to insert javascript to be run in the browser after the submission is loaded
        tojson["feedback_script"] = "".join(self.plugin_manager.call_hook("feedback_script", task=task, submission=data))

        return json.dumps(tojson, default=str)


class TaskPageStaticDownload(INGIniousPage):
    """ Allow to download files stored in the task folder """

    def is_lti_page(self):
        # authorize LTI sessions to download static files
        return True

    def GET(self, courseid, taskid, path):  # pylint: disable=arguments-differ
        """ GET request """
        try:
            course = self.course_factory.get_course(courseid)
            if not self.user_manager.course_is_open_to_user(course):
                return self.template_helper.get_renderer().course_unavailable()

            task = course.get_task(taskid)
            if not self.user_manager.task_is_visible_by_user(task):  # ignore LTI check here
                return self.template_helper.get_renderer().task_unavailable()

            path_norm = posixpath.normpath(urllib.parse.unquote(path))

            public_folder = task.get_fs().from_subfolder("public")
            (method, mimetype_or_none, file_or_url) = public_folder.distribute(path_norm, False)

            if method == "local":
                web.header('Content-Type', mimetype_or_none)
                return file_or_url
            elif method == "url":
                raise web.redirect(file_or_url)
            else:
                raise web.notfound()
        except web.HTTPError as error_or_redirect:
            raise error_or_redirect
        except:
            if web.config.debug:
                raise
            else:
                raise web.notfound()


class TaskPage(INGIniousPage):
    def GET(self, courseid, taskid):
        return BaseTaskPage(self).GET(courseid, taskid, False)

    def POST(self, courseid, taskid):
        return BaseTaskPage(self).POST(courseid, taskid, False)
