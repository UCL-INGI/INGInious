from inginious.frontend.plugins.utils import create_static_resource_page
from inginious.frontend.plugins.problem_bank.constants import _REACT_BASE_URL, _REACT_BUILD_FOLDER, _BASE_STATIC_FOLDER, _BASE_STATIC_URL

from .pages.api.copy_task_api import CopyTaskApi
from .pages.api.manage_banks_courses_api import ManageBanksCoursesApi
from .pages.api.search_task_api import SearchTaskApi
from .pages.api.available_courses_api import AvailableCoursesApi
from .pages.api.filter_tasks_api import FilterTasksApi
from .pages.bank_page import BankPage


def init(plugin_manager, course_factory, client, config):
    if "problem_banks" not in plugin_manager.get_database().collection_names():
        plugin_manager.get_database().create_collection("problem_banks")
    plugin_manager.get_database().problem_banks.create_index([("courseid", 1)], unique=True)

    plugin_manager.add_page(_REACT_BASE_URL + r'(.*)', create_static_resource_page(_REACT_BUILD_FOLDER))
    plugin_manager.add_page(_BASE_STATIC_URL + r'(.*)', create_static_resource_page(_BASE_STATIC_FOLDER))
    plugin_manager.add_page('/plugins/problems_bank/api/copy_task', CopyTaskApi)
    plugin_manager.add_page('/plugins/problems_bank/api/bank_courses', ManageBanksCoursesApi)
    plugin_manager.add_page('/plugins/problems_bank/api/available_courses', AvailableCoursesApi)
    plugin_manager.add_page('/plugins/problems_bank/api/bank_tasks', SearchTaskApi)
    plugin_manager.add_page('/plugins/problems_bank/api/filter_bank_tasks', FilterTasksApi)
    plugin_manager.add_page(r'/plugins/problems_bank', BankPage)
