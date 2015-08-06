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
""" Main page for the LTI provider. Displays a task and allow to answer to it. """
import base64
import json
import mimetypes
import urllib
import web
from inginious.frontend.common.task_page_helpers import list_multiple_multiple_choices_and_files, submission_to_json
from inginious.frontend.lti.pages.utils import LTIAuthenticatedPage


class LTITask(LTIAuthenticatedPage):

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
                mime_type = mimetypes.guess_type(urllib.pathname2url(sinput[userinput["questionid"]]['filename']))
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
                return json.dumps({"status": "error", "text": "Please answer to all the questions. Your responses were not tested."})
            del userinput['@action']

            # Get debug info if the current user is an admin
            debug = "Administrator" in self.user_manager.session_roles()

            # Start the submission
            submissionid = self.submission_manager.add_job(self.task, userinput, debug)

            web.header('Content-Type', 'application/json')
            return json.dumps({"status": "ok", "submissionid": str(submissionid)})
        elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
            if self.submission_manager.is_done(userinput['submissionid']):
                web.header('Content-Type', 'application/json')
                result = self.submission_manager.get_submission(userinput['submissionid'])
                result = self.submission_manager.get_input_from_submission(result)
                result = self.submission_manager.get_feedback_from_submission(result)
                return submission_to_json(result, "Administrator" in self.user_manager.session_roles())
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
            return submission_to_json(submission, "Administrator" in self.user_manager.session_roles(), True)
        else:
            # Display the task itself
            return self.template_helper.get_renderer().task(self.course, self.task, self.submission_manager.get_user_submissions(self.task))
