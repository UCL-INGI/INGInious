# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Task page """
import base64
import json
import mimetypes
import os
import posixpath
import urllib

import web

from bson.objectid import ObjectId
from inginious.frontend.common.task_page_helpers import submission_to_json, list_multiple_multiple_choices_and_files
from inginious.frontend.webapp.pages.utils import INGIniousPage


class TaskPage(INGIniousPage):
    """ Display a task (and allow to reload old submission/file uploaded during a submission) """

    def GET(self, courseid, taskid):
        """ GET request """
        if self.user_manager.session_logged_in():
            username = self.user_manager.session_username()
            try:
                course = self.course_factory.get_course(courseid)
                if not self.user_manager.course_is_open_to_user(course, username):
                    return self.template_helper.get_renderer().course_unavailable()

                task = course.get_task(taskid)
                if not self.user_manager.task_is_visible_by_user(task, username):
                    return self.template_helper.get_renderer().task_unavailable()

                self.user_manager.user_saw_task(username, courseid, taskid)

                userinput = web.input()
                if "submissionid" in userinput and "questionid" in userinput:
                    # Download a previously submitted file
                    submission = self.submission_manager.get_submission(userinput["submissionid"], True)
                    if submission is None:
                        raise web.notfound()
                    sinput = self.submission_manager.get_input_from_submission(submission, True)
                    if userinput["questionid"] not in sinput:
                        raise web.notfound()

                    if isinstance(sinput[userinput["questionid"]], dict):
                        # File uploaded previously
                        mimetypes.init()
                        mime_type = mimetypes.guess_type(urllib.pathname2url(sinput[userinput["questionid"]]['filename']))
                        web.header('Content-Type', mime_type[0])
                        return base64.b64decode(sinput[userinput["questionid"]]['value'])
                    else:
                        # Other file, download it as text
                        web.header('Content-Type', 'text/plain')
                        return sinput[userinput["questionid"]]
                else:
                    user_task = self.database.user_tasks.find_one({
                        "courseid": task.get_course_id(),
                        "taskid": task.get_id(),
                        "username": self.user_manager.session_username()
                    })

                    submissionid = user_task.get('submissionid', None)
                    eval_submission = self.database.submissions.find_one({'_id': ObjectId(submissionid)})

                    students = None
                    if task.is_group_task() and not self.user_manager.has_admin_rights_on_course(course, username):
                        for index, group in enumerate(self.user_manager.get_course_user_aggregation(course)["groups"]):
                            if self.user_manager.session_username() in group["students"]:
                                students = group["students"]
                    else:
                        students = [username]

                    # Display the task itself
                    return self.template_helper.get_renderer().task(course, task,
                                                                    self.submission_manager.get_user_submissions(task),
                                                                    students, eval_submission, self.remote_ssh_manager.is_active())
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_fields(), False)

    def POST(self, courseid, taskid):
        """ POST a new submission """
        if self.user_manager.session_logged_in():
            username = self.user_manager.session_username()

            try:
                course = self.course_factory.get_course(courseid)
                if not self.user_manager.course_is_open_to_user(course, username):
                    return self.template_helper.get_renderer().course_unavailable()

                task = course.get_task(taskid)
                if not self.user_manager.task_is_visible_by_user(task, username):
                    return self.template_helper.get_renderer().task_unavailable()

                self.user_manager.user_saw_task(username, courseid, taskid)

                is_staff = self.user_manager.has_staff_rights_on_course(course, username)
                is_admin = self.user_manager.has_admin_rights_on_course(course, username)

                userinput = web.input()
                if "@action" in userinput and userinput["@action"] == "submit":
                    # Verify rights
                    if not self.user_manager.task_can_user_submit(task, username):
                        return json.dumps({"status": "error", "text": "You are not allowed to submit for this task."})

                    # Reparse user input with array for multiple choices
                    init_var = list_multiple_multiple_choices_and_files(task)
                    userinput = task.adapt_input_for_backend(web.input(**init_var))

                    if not task.input_is_consistent(userinput, self.default_allowed_file_extensions, self.default_max_file_size):
                        web.header('Content-Type', 'application/json')
                        return json.dumps({"status": "error", "text": "Please answer to all the questions and verify the extensions of the files "
                                                                      "you want to upload. Your responses were not tested."})
                    del userinput['@action']

                    # Get debug info if the current user is an admin
                    debug = is_admin
                    if "@debug-mode" in userinput:
                        if userinput["@debug-mode"] == "ssh" and debug and self.remote_ssh_manager.is_active():
                            debug = "ssh"
                        del userinput['@debug-mode']

                    # Start the submission
                    submissionid = self.submission_manager.add_job(task, userinput, debug)

                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "ok", "submissionid": str(submissionid)})
                elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
                    result = self.submission_manager.get_submission(userinput['submissionid'])
                    if result is None:
                        web.header('Content-Type', 'application/json')
                        return json.dumps({'status': "error"})
                    elif self.submission_manager.is_done(result):
                        web.header('Content-Type', 'application/json')
                        result = self.submission_manager.get_input_from_submission(result)
                        result = self.submission_manager.get_feedback_from_submission(result, show_everything=is_staff)

                        user_task = self.database.user_tasks.find_one({
                                     "courseid":task.get_course_id(),
                                     "taskid": task.get_id(),
                                     "username": self.user_manager.session_username()
                                 })

                        submissionid = user_task.get('submissionid', None)
                        default_submission = self.database.submissions.find_one({'_id': ObjectId(submissionid)})
                        return submission_to_json(result, is_admin, False, True if default_submission is None else default_submission['_id'] == result['_id'])

                    else:
                        web.header('Content-Type', 'application/json')
                        if "ssh_key" in result and self.remote_ssh_manager.is_active():
                            return json.dumps({'status': "waiting",
                                               'ssh_host': self.remote_ssh_manager.get_url(),
                                               'ssh_key': result["ssh_key"],
                                               'ssh_conn_id': userinput['submissionid']})
                        else:
                            return json.dumps({'status': "waiting"})
                elif "@action" in userinput and userinput["@action"] == "load_submission_input" and "submissionid" in userinput:
                    submission = self.submission_manager.get_submission(userinput["submissionid"])
                    submission = self.submission_manager.get_input_from_submission(submission)
                    submission = self.submission_manager.get_feedback_from_submission(submission, show_everything=is_staff)
                    if not submission:
                        raise web.notfound()
                    web.header('Content-Type', 'application/json')
                    return submission_to_json(submission, is_admin, True)
                elif "@action" in userinput and userinput["@action"] == "kill" and "submissionid" in userinput:
                    self.submission_manager.kill_running_submission(userinput["submissionid"])  # ignore return value
                    web.header('Content-Type', 'application/json')
                    return json.dumps({'status': 'done'})
                elif "@action" in userinput and userinput["@action"] == "set_submission" and "submissionid" in userinput:
                    web.header('Content-Type', 'application/json')
                    if task.get_evaluate() != 'student':
                        return json.dumps({'status': "error"})

                    submission = self.submission_manager.get_submission(userinput["submissionid"])

                    # Check if task is done per group/team
                    students = None
                    if task.is_group_task() and not is_admin:
                        for index, group in enumerate(self.user_manager.get_course_user_aggregation(course)["groups"]):
                            if self.user_manager.session_username() in group["students"]:
                                students = group["students"]
                    else:
                        students = [username]

                    # Check if group/team is the same
                    if students == submission["username"]:
                        self.database.user_tasks.update_many({"courseid": courseid, "taskid": taskid, "username": {"$in": students}},
                                                                     {"$set": {"submissionid": submission['_id'],
                                                                               "grade": submission['grade'],
                                                                               "succeeded": submission["result"] == "success"}})
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
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_fields(), False)


class TaskPageStaticDownload(INGIniousPage):
    """ Allow to download files stored in the task folder """

    def GET(self, courseid, taskid, path):
        """ GET request """
        if self.user_manager.session_logged_in():
            try:
                course = self.course_factory.get_course(courseid)
                if not self.user_manager.course_is_open_to_user(course):
                    return self.template_helper.get_renderer().course_unavailable()

                task = course.get_task(taskid)
                if not self.user_manager.task_is_visible_by_user(task):
                    return self.template_helper.get_renderer().task_unavailable()

                path_norm = posixpath.normpath(urllib.unquote(path))
                public_folder_path = os.path.normpath(os.path.realpath(os.path.join(task.get_directory_path(), "public")))
                file_path = os.path.normpath(os.path.realpath(os.path.join(public_folder_path, path_norm)))

                # Verify that we are still inside the public directory
                if os.path.normpath(os.path.commonprefix([public_folder_path, file_path])) != public_folder_path:
                    raise web.notfound()

                if os.path.isfile(file_path):
                    mimetypes.init()
                    mime_type = mimetypes.guess_type(file_path)
                    web.header('Content-Type', mime_type[0])
                    with open(file_path) as static_file:
                        return static_file.read()
                else:
                    raise web.notfound()
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_fields(), False)
