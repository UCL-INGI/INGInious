# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" Task page """
import base64
import json
import mimetypes
import os
import posixpath
import urllib

import web

from inginious.common.tasks_code_boxes import FileBox
from inginious.common.tasks_problems import MultipleChoiceProblem, BasicCodeProblem
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
                    # Display the task itself
                    return self.template_helper.get_renderer().task(course, task, self.submission_manager.get_user_submissions(task))
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_inputs(), False)

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
                        return json.dumps({"status": "error", "text": "Please answer to all the questions. Your responses were not tested."})
                    del userinput['@action']

                    # Get debug info if the current user is an admin
                    debug = self.user_manager.has_admin_rights_on_course(course, username)

                    # Start the submission
                    submissionid = self.submission_manager.add_job(task, userinput, debug)

                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "ok", "submissionid": str(submissionid)})
                elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
                    if self.submission_manager.is_done(userinput['submissionid']):
                        web.header('Content-Type', 'application/json')
                        result = self.submission_manager.get_submission(userinput['submissionid'])
                        result = self.submission_manager.get_input_from_submission(result)
                        result = self.submission_manager.get_feedback_from_submission(result)
                        return submission_to_json(result, self.user_manager.has_admin_rights_on_course(course, username))
                    else:
                        web.header('Content-Type', 'application/json')
                        return json.dumps({'status': "waiting"})
                elif "@action" in userinput and userinput["@action"] == "load_submission_input" and "submissionid" in userinput:
                    submission = self.submission_manager.get_submission(userinput["submissionid"])
                    submission = self.submission_manager.get_input_from_submission(submission)
                    submission = self.submission_manager.get_feedback_from_submission(submission)
                    if not submission:
                        raise web.notfound()
                    web.header('Content-Type', 'application/json')
                    return submission_to_json(submission, self.user_manager.has_admin_rights_on_course(course, username), True)
                else:
                    raise web.notfound()
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_inputs(), False)


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
            return self.template_helper.get_renderer().index(self.user_manager.get_auth_methods_inputs(), False)
