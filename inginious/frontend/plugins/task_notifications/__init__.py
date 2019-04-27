# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" INGInious plugin that notifies user agents on task completion. """

import json
from functools import partial

_script = """
let params = {params_obj};
if (localStorage.getItem("taskNotifications") === "on") {{
    new Notification(params.taskName, {{
        body: `Task finished (${{params.result}}). Your score is ${{params.grade}}%.`
    }});
}}
"""

def on_feedback_script(plugin_manager, submission, task, reloading):
    if reloading:
        return ''

    params_json = json.dumps({
        'taskName': task.get_name(plugin_manager.get_user_manager().session_language()),
        'grade': submission['grade'],
        'result': submission['result'],
    })

    return _script.format(params_obj=params_json)

def navbar(template_helper):
    template_helper.add_javascript('/static/plugins/task_notifications/task_notifications.js')
    return str(template_helper.get_custom_renderer('frontend/plugins/task_notifications', layout=False).navbar())

def init(plugin_manager, course_factory, client, plugin_config):  # pylint: disable=unused-argument
    plugin_manager.add_hook('feedback_script', partial(on_feedback_script, plugin_manager))
    plugin_manager.add_hook('navbar', navbar)
