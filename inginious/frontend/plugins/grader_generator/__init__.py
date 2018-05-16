import os

from inginious.frontend.plugins.utils import create_static_resource_page
from .pages.api.task_test_cases_files_api import TaskTestCasesFilesApi

from .pages.grader import on_task_editor_submit
from .pages.grader import grader_footer
from .pages.grader import grader_generator_tab

_BASE_STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')


def init(plugin_manager, course_factory, client, config):
    plugin_manager.add_page(r'/grader_generator/static/(.*)', create_static_resource_page(_BASE_STATIC_FOLDER))

    plugin_manager.add_page('/api/grader_generator/test_file_api', TaskTestCasesFilesApi)

    plugin_manager.add_hook('task_editor_tab', grader_generator_tab)
    plugin_manager.add_hook('task_editor_footer', grader_footer)
    plugin_manager.add_hook('task_editor_submit', on_task_editor_submit)
