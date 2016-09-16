# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A simple job manager for EDX """
import json

import web

from inginious.client.client_sync import ClientSync
from inginious.frontend.webapp.pages.utils import INGIniousPage


def init(plugin_manager, course_factory, client, config):
    """
        Init the edx plugin.
        Available configuration:
        ::

            {
                "plugin_module": "webapp.plugins.edx",
                "courseid": "edx",
                "page_pattern": "/edx"
            }

    """
    courseid = config.get('courseid', 'edx')
    course = course_factory.get_course(courseid)
    page_pattern = config.get('page_pattern', '/edx')

    client_sync = ClientSync(client)

    class EDX(INGIniousPage):

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

            post_input = web.data()

            try:
                decoded_input = json.loads(post_input)
            except:
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: cannot decode POST</p>"})

            if "xqueue_body" not in decoded_input:
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: no xqueue_body in POST</p>"})
            try:
                edx_input = json.loads(decoded_input["xqueue_body"])
                taskid = json.loads(edx_input["grader_payload"])["tid"]
            except:
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: cannot decode JSON</p>"})

            try:
                task = course.get_task(taskid)
            except:
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: unknown task {}</p>".format(taskid)})

            if not task.input_is_consistent(edx_input, self.default_allowed_file_extensions, self.default_max_file_size):
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: input not consistent with task</p>"})

            try:
                job_return = client_sync.new_job(task, edx_input, "Plugin - EDX")
            except:
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: error while grading submission</p>"})

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

                import tidylib

                out, dummy = tidylib.tidy_fragment(text, options={'output-xhtml': 1, 'enclose-block-text': 1, 'enclose-text': 1})
                return json.dumps({"correct": (True if (job_return["result"] == "success") else None), "score": score, "msg": out})
            except:
                return json.dumps({"correct": None, "score": 0, "msg": "<p>Internal grader error: error converting submission result</p>"})

    plugin_manager.add_page(page_pattern, EDX)
