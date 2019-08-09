# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Allow the webapp to act as a simple POST grader """
import json
import re

import web

from inginious.client.client_buffer import ClientBuffer
from inginious.client.client_sync import ClientSync
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.courses import WebAppCourse

def init(plugin_manager, client, config):
    """
        Init the external grader plugin. This simple grader allows only anonymous requests, and submissions are not stored in database.

        Available configuration:
        ::

            plugins:
                - plugin_module: inginious.frontend.plugins.simple_grader
                  courseid : "external"
                  page_pattern: "/external"
                  return_fields: "^(result|text|problems)$"

        The grader will only return fields that are in the job return dict if their key match return_fields.

        Different types of request are available : see documentation
    """
    courseid = config.get('courseid', 'external')
    page_pattern = config.get('page_pattern', '/external')
    return_fields = re.compile(config.get('return_fields', '^(result|text|problems)$'))

    client_buffer = ClientBuffer(client)
    client_sync = ClientSync(client)

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
                        <textarea style="width:100%; height:400px;" name="input">{"question1":"print 'Hello World!'"}</textarea><br/>
                        <input type="text" name="taskid" value="helloworld"/> (taskid)<br/>
                        <input type="checkbox" name="async"/> async?<br/>
                        <input type="submit"/>
                    </form>
                </body>
            </html>"""

        def keep_only_config_return_values(self, job_return):
            """ Keep only some useful return values """
            return {key: value for key, value in job_return.items() if return_fields.match(key)}

        def POST(self):
            """ POST request """
            course = self.database.courses.find_one({"_id": courseid})
            course = WebAppCourse(course["_id"], course, self.filesystem, self.plugin_manager)

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
                        result, grade, problems, tests, custom, state, archive, stdout, stderr = client_sync.new_job(task, task_input, "Plugin - Simple Grader")
                        job_return = {"result":result, "grade": grade, "problems": problems, "tests": tests, "custom": custom, "state": state, "archive": archive, "stdout": stdout, "stderr": stderr}
                    except:
                        return json.dumps({"status": "error", "status_message": "An internal error occurred"})

                    return json.dumps(dict(list({"status": "done"}.items()) + list(self.keep_only_config_return_values(job_return).items())))
                else:
                    # New async job
                    jobid = client_buffer.new_job(task, task_input, "Plugin - Simple Grader")
                    return json.dumps({"status": "done", "jobid": str(jobid)})
            elif "jobid" in post_input:
                # Get status of async job
                if client_buffer.is_waiting(post_input["jobid"]):
                    return json.dumps({"status": "waiting"})
                elif client_buffer.is_done(post_input["jobid"]):
                    result, grade, problems, tests, custom, state, archive, stdout, stderr = client_buffer.get_result(post_input["jobid"])
                    job_return = {"result": result, "grade": grade, "problems": problems, "tests": tests,
                                  "custom": custom, "archive": archive, "stdout": stdout, "stderr": stderr}
                    return json.dumps(dict(list({"status": "done"}.items()) + list(self.keep_only_config_return_values(job_return).items())))
                else:
                    return json.dumps({"status": "error", "status_message": "There is no job with jobid {}".format(post_input["jobid"])})
            else:
                return json.dumps({"status": "error", "status_message": "Unknown request type"})

    plugin_manager.add_page(page_pattern, ExternalGrader)
