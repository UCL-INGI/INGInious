import os
from inginious.frontend.plugins.utils import create_static_resource_page

from inginious.frontend.plugins.statistics.pages.api.admin.grade_count_details import GradeCountDetailsApi
from inginious.frontend.plugins.statistics.pages.course_admin_statistics import CourseAdminStatisticsPage
from inginious.frontend.plugins.statistics.pages.course_admin_statistics import statistics_course_admin_menu_hook
from inginious.frontend.plugins.statistics.pages.api.admin.grade_count import GradeCountApi
from inginious.frontend.plugins.statistics.pages.api.admin.best_submissions_by_verdict import BestSubmissionsByVerdictApi

_static_folder_path = os.path.join(os.path.dirname(__file__), "static")

def init(plugin_manager, course_factory, client, config):
    plugin_manager.add_page(r'/statistics/static/(.*)', create_static_resource_page(_static_folder_path))

    plugin_manager.add_page(r'/admin/([a-z0-9A-Z\-_]+)/statistics', CourseAdminStatisticsPage)
    plugin_manager.add_hook('course_admin_menu', statistics_course_admin_menu_hook)

    plugin_manager.add_page('/api/stats/admin/grade_count', GradeCountApi)
    plugin_manager.add_page('/api/stats/admin/best_submissions_verdict', BestSubmissionsByVerdictApi)
    plugin_manager.add_page('/api/stats/admin/grade_count_details', GradeCountDetailsApi)
