# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Main page for the LTI provider. Displays a task and allow to answer to it. """
import base64
import json
import mimetypes
import urllib.request, urllib.parse, urllib.error

import web

from inginious.frontend.common.task_page_helpers import list_multiple_multiple_choices_and_files, submission_to_json
from inginious.frontend.lti.pages.utils import LTIAuthenticatedPage


class LTITask(LTIAuthenticatedPage):
    def LTI_GET_NOT_CONNECTED(self):
        return self.LTI_POST_NOT_CONNECTED()

    def LTI_POST_NOT_CONNECTED(self):
        userinput = web.input()
        if "@action" in userinput:
            web.header('Content-Type', 'application/json')
            return json.dumps({"status": "error", "text": "Your session have expired. Copy your work and reload the page."})
        return super(LTITask, self).LTI_POST_NOT_CONNECTED()

    def LTI_GET(self):
        return self.LTI_POST()

    def LTI_POST(self):
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
            debug = "Administrator" in self.user_manager.session_roles()

            # Start the submission
            submissionid, oldsubids = self.submission_manager.add_job(self.task, userinput, debug)

            web.header('Content-Type', 'application/json')
            return json.dumps({"status": "ok", "submissionid": str(submissionid), "remove": oldsubids})
        elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
            if self.submission_manager.is_done(userinput['submissionid']):
                web.header('Content-Type', 'application/json')
                result = self.submission_manager.get_submission(userinput['submissionid'])
                result = self.submission_manager.get_input_from_submission(result)
                result = self.submission_manager.get_feedback_from_submission(result,
                                                                              show_everything="Administrator" in self.user_manager.session_roles())
                return submission_to_json(result, "Administrator" in self.user_manager.session_roles())
            else:
                web.header('Content-Type', 'application/json')
                return json.dumps({'status': "waiting"})
        elif "@action" in userinput and userinput["@action"] == "load_submission_input" and "submissionid" in userinput:
            submission = self.submission_manager.get_submission(userinput["submissionid"])
            submission = self.submission_manager.get_input_from_submission(submission)
            submission = self.submission_manager.get_feedback_from_submission(submission,
                                                                              show_everything="Administrator" in self.user_manager.session_roles())
            if not submission:
                raise web.notfound()
            web.header('Content-Type', 'application/json')
            return submission_to_json(submission, "Administrator" in self.user_manager.session_roles(), True)
        elif "@action" in userinput and userinput["@action"] == "kill" and "submissionid" in userinput:
            self.submission_manager.kill_running_submission(userinput["submissionid"])  # ignore return value
            web.header('Content-Type', 'application/json')
            return json.dumps({'status': 'done'})
        else:
            # Display the task itself
            return self.template_helper.get_renderer().task(self.course, self.task, self.submission_manager.get_user_submissions(self.task))
