import os
import web
import json

from inginious.frontend.plugins.utils import create_static_resource_page, get_mandatory_parameter
from inginious.client.client_sync import ClientSync
from inginious.frontend.pages.api._api_page import APIAuthenticatedPage
from inginious.frontend.parsable_text import ParsableText

_static_folder_path = os.path.join(os.path.dirname(__file__), "static")

def customInputManagerWithCurriedClient(client):
    class CustomInputManager(APIAuthenticatedPage):
        def __init__(self):
            self._client = client

        def add_unsaved_job(self, task, inputdata):
            temp_client = ClientSync(self._client)
            return temp_client.new_job(task, inputdata)

        def API_POST(self):
            request_params = web.input()
            courseid = get_mandatory_parameter(request_params, "courseid")
            course = self.course_factory.get_course(courseid)
            taskid = get_mandatory_parameter(request_params, "taskid")
            task = self.task_factory.get_task(course, taskid)

            try:
                init_var = {
                    problem.get_id(): problem.input_type()()
                    for problem in task.get_problems() if problem.input_type() in [dict, list]
                }
                
                userinput = task.adapt_input_for_backend(web.input(**init_var))
                result, grade, problems, tests, custom, archive, stdout, stderr = self.add_unsaved_job(task, userinput)

                data = {
                    "status": ("done" if result[0] == "success" or result[0] == "failed" else "error"),
                    "result": result[0],
                    "text": ParsableText(result[1]).parse(),
                    "stdout": custom.get("custom_stdout", ""),
                    "stderr": custom.get("custom_stderr", "")
                }

                web.header('Content-Type', 'application/json')
                return 200, json.dumps(data)

            except Exception as ex:
                web.header('Content-Type', 'application/json')
                return 200, json.dumps({"status": "error", "text": str(ex)})

    return CustomInputManager

def init(plugin_manager, course_factory, client, plugin_config):
    plugin_manager.add_page(r'/custom_input/static/(.*)', create_static_resource_page(_static_folder_path))
    plugin_manager.add_page("/api/custom_input/", customInputManagerWithCurriedClient(client))
    plugin_manager.add_hook("javascript_header", lambda: "/custom_input/static/custom_input.js")
