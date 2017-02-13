# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Main page for the LTI provider. Displays a task and allow to answer to it. """
import os
import posixpath
import base64
import json
import logging
import mimetypes
import urllib.request, urllib.parse, urllib.error

import web

from inginious.frontend.common.task_page_helpers import list_multiple_multiple_choices_and_files, submission_to_json
from inginious.frontend.lti.pages.utils import LTIAuthenticatedPage


class LTITask(LTIAuthenticatedPage):

    _logger = logging.getLogger("inginious.lti.tasks")

    def LTI_GET_NOT_CONNECTED(self):
        self._logger.debug('LTI_GET_NOT_CONNECTED')
        return self.LTI_POST_NOT_CONNECTED()

    def LTI_POST_NOT_CONNECTED(self):
        self._logger.debug('LTI_POST_NOT_CONNECTED')
        userinput = web.input()
        if "@action" in userinput:
            web.header('Content-Type', 'application/json')
            return json.dumps({"status": "error", "text": "Your session have expired. Copy your work and reload the page."})
        return super(LTITask, self).LTI_POST_NOT_CONNECTED()

    def LTI_GET(self):
        self._logger.debug('LTI_GET')
        return self.LTI_POST()

    def LTI_POST(self):
        userinput = web.input()

        self._logger.debug('post with userinput=' + str(userinput))

        is_admin = any(x in self.admin_role for x in self.user_manager.session_roles())

        # TODO: this is nearly the same as the code in the webapp.
        # We should refactor this.

        if "submissionid" in userinput and "questionid" in userinput:
            # Download a previously submitted file
            submission = self.submission_manager.get_submission(userinput["submissionid"], True)
            if submission is None:
                self._logger.info('Error: submission not found')
                raise web.notfound()
            sinput = self.submission_manager.get_input_from_submission(submission, True)
            if userinput["questionid"] not in sinput:
                self._logger.info('Error: questionid not found')
                raise web.notfound()

            if isinstance(sinput[userinput["questionid"]], dict):
                # File uploaded previously
                mimetypes.init()
                mime_type = mimetypes.guess_type(urllib.request.pathname2url(sinput[userinput["questionid"]]['filename']))
                web.header('Content-Type', mime_type[0])
                return base64.b64decode(sinput[userinput["questionid"]]['value'])
            else:
                # Other file, download it as text
                web.header('Content-Type', 'text/plain')
                return sinput[userinput["questionid"]]
        elif "@action" in userinput and userinput["@action"] == "submit":
            # Reparse user input with array for multiple choices
            init_var = list_multiple_multiple_choices_and_files(self.task)
            userinput = self.task.adapt_input_for_backend(web.input(**init_var))

            if not self.task.input_is_consistent(userinput, self.default_allowed_file_extensions, self.default_max_file_size):
                web.header('Content-Type', 'application/json')
                return json.dumps({"status": "error", "text": "Please answer to all the questions and verify the extensions of the files you want "
                                                              "to upload. Your responses were not tested."})
            del userinput['@action']

            # Get debug info if the current user is an admin
            debug = is_admin
            if "@debug-mode" in userinput:
                if userinput["@debug-mode"] == "ssh" and debug:
                    debug = "ssh"
                del userinput['@debug-mode']

            # Start the submission
            try:
                submissionid, oldsubids = self.submission_manager.add_job(self.task, userinput, debug)
                web.header('Content-Type', 'application/json')
                return json.dumps({"status": "ok", "submissionid": str(submissionid), "remove": oldsubids})
            except Exception as ex:
                web.header('Content-Type', 'application/json')
                return json.dumps({"status": "error", "text": str(ex)})

        elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
            result = self.submission_manager.get_submission(userinput['submissionid'])
            if result is None:
                web.header('Content-Type', 'application/json')
                return json.dumps({'status': "error"})
            elif self.submission_manager.is_done(result):
                web.header('Content-Type', 'application/json')
                result = self.submission_manager.get_submission(userinput['submissionid'])
                result = self.submission_manager.get_input_from_submission(result)
                result = self.submission_manager.get_feedback_from_submission(result,
                                                                              show_everything=is_admin)
                return submission_to_json(result, is_admin)
            else:
                web.header('Content-Type', 'application/json')
                if "ssh_host" in result:
                    return json.dumps({'status': "waiting",
                                       'ssh_host': result["ssh_host"],
                                       'ssh_port': result["ssh_port"],
                                       'ssh_password': result["ssh_password"]})
                # Here we are waiting. Let's send some useful information.
                waiting_data = self.submission_manager.get_job_queue_info(result["jobid"]) if "jobid" in result else None
                if waiting_data is not None:
                    nb_tasks_before, approx_wait_time = waiting_data
                    return json.dumps({'status': "waiting", 'nb_tasks_before': nb_tasks_before, 'approx_wait_time': approx_wait_time})
                return json.dumps({'status': "waiting"})
        elif "@action" in userinput and userinput["@action"] == "load_submission_input" and "submissionid" in userinput:
            submission = self.submission_manager.get_submission(userinput["submissionid"])
            submission = self.submission_manager.get_input_from_submission(submission)
            submission = self.submission_manager.get_feedback_from_submission(submission,
                                                                              show_everything=is_admin)
            if not submission:
                self._logger.info('ERROR: not submission')
                raise web.notfound()
            web.header('Content-Type', 'application/json')
            return submission_to_json(submission, is_admin, True)
        elif "@action" in userinput and userinput["@action"] == "kill" and "submissionid" in userinput:
            self.submission_manager.kill_running_submission(userinput["submissionid"])  # ignore return value
            web.header('Content-Type', 'application/json')
            return json.dumps({'status': 'done'})
        else:
            # Display the task itself
            return self.template_helper.get_renderer().task(self.course, self.task, self.submission_manager.get_user_submissions(self.task), is_admin, self.webterm_link)


class LTITaskPageStaticDownload(LTIAuthenticatedPage):
    """ Allow to download files stored in the task folder """

    def LTI_GET(self, taskid, path):  # pylint: disable=arguments-differ
        """ GET request """
        try:
            if not taskid == self.task.get_id():
                raise web.notfound()

            path_norm = posixpath.normpath(urllib.parse.unquote(path))
            public_folder_path = os.path.normpath(os.path.realpath(os.path.join(self.task.get_directory_path(), "public")))
            file_path = os.path.normpath(os.path.realpath(os.path.join(public_folder_path, path_norm)))

            # Verify that we are still inside the public directory
            if os.path.normpath(os.path.commonprefix([public_folder_path, file_path])) != public_folder_path:
                raise web.notfound()

            if os.path.isfile(file_path):
                mimetypes.init()
                mime_type = mimetypes.guess_type(file_path)
                web.header('Content-Type', mime_type[0])
                return open(file_path, 'rb')
            else:
                raise web.notfound()
        except:
            if web.config.debug:
                raise
            else:
                raise web.notfound()
