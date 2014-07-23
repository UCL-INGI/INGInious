""" A simple job manager for EDX """
import json
import threading

import web

from common.courses import Course
import frontend.submission_manager


def init(plugin_manager, config):
    """
        Init the edx plugin.
        Available configuration:
        ::

            {
                "plugin_module": "frontend.plugins.edx",
                "courseid": "edx",
                "page_pattern": "/edx"
            }

    """
    courseid = config.get('courseid', 'edx')
    course = Course(courseid)
    page_pattern = config.get('page_pattern', '/edx')

    class EDX(object):

        """ Manages job from EDX """

        def GET(self):
            """ GET request """
            return """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>EDX test</title>
                </head>
                <body>
                    <form method="post">
                        <textarea style="width:100%; height:400px;" name="xqueue_body">{
        "student_response": "def double(x):\\n return 2*x\\n",
        "grader_payload": "basic"
    }</textarea><br/>
                        <input type="submit"/>
                    </form>
                </body>
            </html>"""

        def POST(self):
            """ POST request """
            web.header('Content-Type', 'application/json')
            post_input = web.input()
            if "xqueue_body" not in post_input:
                return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: no xqueue_body in POST</p>"})
            try:
                edx_input = json.loads(post_input.xqueue_body)
                taskid = edx_input["grader_payload"]
            except:
                return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: cannot decode JSON</p>"})

            try:
                task = course.get_task(taskid)
            except:
                return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: unknown task</p>"})

            if not task.input_is_consistent(edx_input):
                return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: input not consistent with task</p>"})

            try:
                job_semaphore = threading.Semaphore(0)

                def manage_output(_, job):
                    """ Manages the output of this job """
                    print "RETURN JOB"
                    manage_output.jobReturn = job
                    job_semaphore.release()
                frontend.submission_manager.get_backend_job_queue().add_job(task, edx_input, manage_output)
                job_semaphore.acquire()
                job_return = manage_output.jobReturn
            except:
                return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: error while grading submission</p>"})

            try:
                text = ""
                if "text" in job_return:
                    text = job_return["text"]
                if "problems" in job_return:
                    for prob in job_return["problems"]:
                        text += "<br/><h4>" + job_return["task"].get_problems()[prob].get_name() + "</h4>" + job_return["problems"][prob]

                score = (1 if job_return["result"] == "success" else 0)
                if "score" in job_return:
                    score = job_return["score"]

                return json.dumps({"correct": (job_return["result"] == "success"), "score": score, "msg": text})
            except:
                return json.dumps({"correct": False, "score": 0, "msg": "<p>Internal grader error: error converting submission result</p>"})

    plugin_manager.add_page(page_pattern, EDX)
