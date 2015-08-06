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
""" A simple job manager for EDX """
import json

import web

from inginious.backend.helpers.job_manager_sync import JobManagerSync
from inginious.frontend.webapp.pages.utils import INGIniousPage


def init(plugin_manager, course_factory, job_manager, config):
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

    job_manager_sync = JobManagerSync(job_manager)

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
                job_return = job_manager_sync.new_job(task, edx_input, "Plugin - EDX")
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
