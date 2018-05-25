from inginious.frontend.plugins.utils import create_static_resource_page
from inginious.frontend.plugins.problem_bank.constants import _REACT_BASE_URL, _REACT_BUILD_FOLDER, _BASE_STATIC_FOLDER,\
    _BASE_STATIC_URL, _BASE_RENDERER_PATH

from .pages.api.copy_task_api import CopyTaskApi
from .pages.api.manage_banks_courses_api import ManageBanksCoursesApi
from .pages.api.available_tasks_api import AvailableTasksApi
from .pages.api.available_courses_api import AvailableCoursesApi
from .pages.api.filter_tasks_api import FilterTasksApi
from .pages.api.available_courses_to_copy_api import AvailableCoursesToCopyApi

from .pages.bank_page import BankPage


def init(plugin_manager, course_factory, client, config):
    def on_course_updated(courseid, new_content):
        course_data = {
            "course_name": new_content["name"]
        }
        data_filter = {
            "courseid": courseid
        }
        plugin_manager.get_database().problem_banks.update_one(filter=data_filter, update={"$set": course_data})

    def problem_bank_course_admin_menu_hook(course):
        if not plugin_manager.get_user_manager().has_admin_rights_on_course(course):
            return None
        else:
            return "problems_bank", '<i class="fa fa-database" aria-hidden="true"></i> Problem bank'

    if "problem_banks" not in plugin_manager.get_database().collection_names():
        plugin_manager.get_database().create_collection("problem_banks")
    plugin_manager.get_database().problem_banks.create_index([("courseid", 1)], unique=True)

    plugin_manager.add_page(_REACT_BASE_URL + r'(.*)', create_static_resource_page(_REACT_BUILD_FOLDER))
    plugin_manager.add_page(_BASE_STATIC_URL + r'(.*)', create_static_resource_page(_BASE_STATIC_FOLDER))

    plugin_manager.add_page('/plugins/problems_bank/api/copy_task', CopyTaskApi)
    plugin_manager.add_page('/plugins/problems_bank/api/bank_courses', ManageBanksCoursesApi)
    plugin_manager.add_page('/plugins/problems_bank/api/available_courses', AvailableCoursesApi)
    plugin_manager.add_page('/plugins/problems_bank/api/bank_tasks', AvailableTasksApi)
    plugin_manager.add_page('/plugins/problems_bank/api/filter_bank_tasks', FilterTasksApi)
    plugin_manager.add_page('/plugins/problems_bank/api/available_courses_to_copy', AvailableCoursesToCopyApi)

    plugin_manager.add_page(r'/admin/([a-z0-9A-Z\-_]+)/problems_bank', BankPage)

    plugin_manager.add_hook('course_admin_menu', problem_bank_course_admin_menu_hook)
    plugin_manager.add_hook('course_updated', on_course_updated)
