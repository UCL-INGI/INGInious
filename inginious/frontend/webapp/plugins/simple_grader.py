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
""" Allow the webapp to act as a simple POST grader """
import json
import re

import web

from inginious.backend.helpers.job_manager_buffer import JobManagerBuffer
from inginious.backend.helpers.job_manager_sync import JobManagerSync
from inginious.frontend.webapp.pages.utils import INGIniousPage


def init(plugin_manager, course_factory, job_manager, config):
    """
        Init the external grader plugin. This simple grader allows only anonymous requests, and submissions are not stored in database.

        Available configuration:
        ::

            {
                "plugin_module": "webapp.plugins.simple_grader",
                "courseid": "external",
                "page_pattern": "/external",
                "return_fields": "^(result|text|problems)$"
            }

        The grader will only return fields that are in the job return dict if their key match return_fields.

        Different types of request are available

        New synchronized job
            External submissions must take the form of a POST request on the url defined by *page_pattern*.
            This POST must contains two data field:

            - *taskid*: the task id of the task

            - *input*: the input for the task, in JSON. The input is a dictionary filled with problemid:problem_answer pairs.

            The return value will contains the standard return fields of an INGInious inginious.backend job plus a "status" field that will
            contain "ok".

            If an internal error occurs, it will return a dictionary containing

            ::

                {
                    "status": "error",
                    "status_message": "A message containing a simple description of the error"
                }

        New asynchronous job
            This POST request allows new jobs to be treated asynchronously.
            It must contains three data fields:

            - *taskid*: the task id of the task

            - *input*: the input for the task, in JSON. The input is a dictionary filled with problemid:problem_answer pairs.

            - *async*: field that indicate that the job must be launched asynchronously. Only have to be present, content is not read.

            The return value will be a dictionnary containing:

            ::

                {

                    "status": "done",
                    "jobid": "the jobid of the async job. Will be needed to get the results."
                }

            or

            ::

                {
                    "status": "error",
                    "status_message": "A message describing the error"
                }

        Get status of asynchronous job
            Given a jobid in input (as field of the POST request) and will return either:

            ::

                {
                    "status": "waiting"
                }

            or

            ::

                {
                    "status": "error",
                    "status_message": "A message describing the error"
                }

            or

            ::

                {
                    "status": "done",
                    "...":"..."
                }

            Where *...* are the results of the job, as defined in the "return_fields" config value.

    """
    courseid = config.get('courseid', 'external')
    course = course_factory.get_course(courseid)
    page_pattern = config.get('page_pattern', '/external')
    return_fields = re.compile(config.get('return_fields', '^(result|text|problems)$'))

    job_manager_buffer = JobManagerBuffer(job_manager)
    job_manager_sync = JobManagerSync(job_manager)

    class ExternalGrader(INGIniousPage):

        """ Manages job from outside, using the default input """

        def GET(self):
            """ GET request """
            return """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>External grade POST test</title>
                </head>
                <body>
                    <form method="post">
                        <textarea style="width:100%; height:400px;" name="input">{"student_response":"{Browse 'Hello World!'}"}</textarea><br/>
                        <input type="text" name="taskid" value="HelloWorld"/> (taskid)<br/>
                        <input type="checkbox" name="async"/> async?<br/>
                        <input type="submit"/>
                    </form>
                </body>
            </html>"""

        def keep_only_config_return_values(self, job_return):
            """ Keep only some useful return values """
            return {key: value for key, value in job_return.iteritems() if return_fields.match(key)}

        def POST(self):
            """ POST request """
            web.header('Access-Control-Allow-Origin', '*')
            web.header('Content-Type', 'application/json')
            post_input = web.input()

            if "input" in post_input and "taskid" in post_input:
                # New job
                try:
                    task_input = json.loads(post_input.input)
                except:
                    return json.dumps({"status": "error", "status_message": "Cannot decode input"})

                try:
                    task = course.get_task(post_input.taskid)
                except:
                    return json.dumps({"status": "error", "status_message": "Cannot open task"})

                if not task.input_is_consistent(task_input, self.default_allowed_file_extensions, self.default_max_file_size):
                    return json.dumps({"status": "error", "status_message": "Input is not consistent with the task"})

                if post_input.get("async") is None:
                    # New sync job
                    try:
                        job_return = job_manager_sync.new_job(task, task_input, "Plugin - Simple Grader")
                    except:
                        return json.dumps({"status": "error", "status_message": "An internal error occured"})

                    return json.dumps(dict({"status": "done"}.items() + self.keep_only_config_return_values(job_return).items()))
                else:
                    # New async job
                    jobid = job_manager_buffer.new_job(task, task_input, "Plugin - Simple Grader")
                    return json.dumps({"status": "done", "jobid": str(jobid)})
            elif "jobid" in post_input:
                # Get status of async job
                if job_manager_buffer.is_waiting(post_input["jobid"]):
                    return json.dumps({"status": "waiting"})
                elif job_manager_buffer.is_done(post_input["jobid"]):
                    job_return = job_manager_buffer.get_result(post_input["jobid"])
                    return json.dumps(dict({"status": "done"}.items() + self.keep_only_config_return_values(job_return).items()))
                else:
                    return json.dumps({"status": "error", "status_message": "There is no job with jobid {}".format(post_input["jobid"])})
            else:
                return json.dumps({"status": "error", "status_message": "Unknown request type"})

    plugin_manager.add_page(page_pattern, ExternalGrader)
