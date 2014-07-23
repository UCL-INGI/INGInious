""" Allow the frontend to act as a simple POST grader """
import json
import re
import threading

import web

from common.courses import Course
import frontend.submission_manager


def init(plugin_manager, config):
    """
        Init the external grader plugin.
        Available configuration:
        ::

            {
                "plugin_module": "frontend.plugins.simple_grader",
                "courseid": "external",
                "page_pattern": "/external",
                "return_fields": "^(result|text|problems)$"
            }

        The grader will only return fields that are in the job return dict if their key match return_fields.

        External submissions must take the form of a POST request on the url defined by *page_pattern*.
        This POST must contains two data field:

        - *taskid*: the task id of the task

        - *input*: the input for the task, in JSON. The input is a dictionary filled with problemid:problem_answers pairs.

    """
    courseid = config.get('courseid', 'external')
    course = Course(courseid)
    page_pattern = config.get('page_pattern', '/external')
    return_fields = re.compile(config.get('return_fields', '^(result|text|problems)$'))

    class ExternalGrader(object):

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
                        <input type="text" name="taskid" value="HelloWorld"/>
                        <input type="submit"/>
                    </form>
                </body>
            </html>"""

        def POST(self):
            """ POST request """
            web.header('Content-Type', 'application/json')
            post_input = web.input()

            if "input" not in post_input or "taskid" not in post_input:
                return json.dumps({"result": "crash", "text": "The json must contain an input field and a taskid"})

            try:
                task_input = json.loads(post_input.input)
            except:
                return json.dumps({"result": "crash", "text": "Cannot decode input"})

            try:
                task = course.get_task(post_input.taskid)
            except:
                return json.dumps({"result": "crash", "text": "Cannot open task"})

            try:
                job_semaphore = threading.Semaphore(0)

                def manage_output(_, job):
                    """ Manages the output of this job """
                    print "RETURN JOB"
                    manage_output.jobReturn = job
                    job_semaphore.release()
                frontend.submission_manager.get_backend_job_queue().add_job(task, task_input, manage_output)
                job_semaphore.acquire()
                job_return = manage_output.jobReturn
            except:
                return json.dumps({"result": "crash", "text": "An internal error occured"})

            return json.dumps({key: value for key, value in job_return.iteritems() if return_fields.match(key)})

    plugin_manager.add_page(page_pattern, ExternalGrader)
