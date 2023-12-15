import json

_BASE_RENDERER_PATH = 'frontend/plugins/task_editor_hook_example'


def example_task_editor_tab(course, taskid, task_data, template_helper):
    tab_id = 'tab_example'
    link = '<i class="fa fa-edit fa-fw"></i>&nbsp; Example tab'
    content = 'This is a test'

    return tab_id, link, content


def example_task_editor_tab_2(course, taskid, task_data, template_helper):
    tab_id = 'tab_example_2'
    link = '<i class="fa fa-edit fa-fw"></i>&nbsp; Example tab 2'
    content = template_helper.render("example_tab_2.html", template_folder=_BASE_RENDERER_PATH,
                                     course=course, taskid=taskid, task_data=task_data)

    return tab_id, link, content


def on_task_editor_submit(course, taskid, task_data, task_fs):
    # We can modify task data here
    task_data['example_field'] = 'test'

    # We can also check for correctness and raise and error if something is wrong
    if not task_data.get('example_task_hint', None):
        return json.dumps({"status": "error", "message": "You must provide a task hint in Example tab 2"})


def init(plugin_manager, taskset_factory, client, config):

    plugin_manager.add_hook('task_editor_tab', example_task_editor_tab)
    plugin_manager.add_hook('task_editor_tab', example_task_editor_tab_2)
    plugin_manager.add_hook('task_editor_submit', on_task_editor_submit)
