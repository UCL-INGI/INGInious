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

        Different types of request are available

        New synchronized job
            External submissions must take the form of a POST request on the url defined by *page_pattern*.
            This POST must contains two data field:

            - *taskid*: the task id of the task

            - *input*: the input for the task, in JSON. The input is a dictionary filled with problemid:problem_answer pairs.

            The return value will contains the standard return fields of an INGInious backend job plus a "status" field that will
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

                    "status": "ok",
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
    course = Course(courseid)
    page_pattern = config.get('page_pattern', '/external')
    return_fields = re.compile(config.get('return_fields', '^(result|text|problems)$'))

    async_job_data = {}

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
                        <input type="text" name="taskid" value="HelloWorld"/> (taskid)<br/>
                        <input type="checkbox" name="async"/> async?<br/>
                        <input type="submit"/>
                    </form>
                </body>
            </html>"""

        def keep_only_config_return_values(self, job_return):
            return {key: value for key, value in job_return.iteritems() if return_fields.match(key)}

        def manage_async_job(self, jobid, _, result):
            async_job_data[jobid] = result

        def POST(self):
            """ POST request """
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

                if post_input.get("async") is None:
                    # New sync job
                    try:
                        job_semaphore = threading.Semaphore(0)

                        def manage_output(dummy1_, dummy2_, job):
                            """ Manages the output of this job """
                            print "RETURN JOB"
                            manage_output.jobReturn = job
                            job_semaphore.release()
                        frontend.submission_manager.get_job_manager().new_job(task, task_input, manage_output)
                        job_semaphore.acquire()
                        job_return = manage_output.jobReturn
                    except:
                        return json.dumps({"status": "error", "status_message": "An internal error occured"})

                    return json.dumps(dict({"status": "ok"}.items() + self.keep_only_config_return_values(job_return).items()))
                else:
                    # New async job
                    jobid = frontend.submission_manager.get_job_manager().new_job(task, task_input, self.manage_async_job)
                    return json.dumps({"status": "ok", "jobid": str(jobid)})
            elif "jobid" in post_input:
                # Get status of async job
                if post_input["jobid"] not in async_job_data:
                    return json.dumps({"status": "waiting"})
                else:
                    job_return = async_job_data[post_input["jobid"]]
                    del async_job_data[post_input["jobid"]]
                    return json.dumps(dict({"status": "ok"}.items() + self.keep_only_config_return_values(job_return).items()))
            else:
                return json.dumps({"status": "error", "status_message": "Unknown request type"})

    plugin_manager.add_page(page_pattern, ExternalGrader)
