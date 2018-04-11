from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from .constants import base_renderer_path

class CourseAdminStatisticsPage(INGIniousAdminPage):
    def GET_AUTH(self, course_id):
        course, _ = self.get_course_and_check_rights(course_id)

        self.template_helper.add_javascript("https://cdnjs.cloudflare.com/ajax/libs/PapaParse/4.3.6/papaparse.min.js")
        self.template_helper.add_javascript("https://cdn.plot.ly/plotly-1.30.0.min.js")
        self.template_helper.add_javascript("https://cdn.jsdelivr.net/npm/lodash@4.17.4/lodash.min.js")
        self.template_helper.add_javascript("/statistics/static/js/statistics.js")
        self.template_helper.add_javascript("/statistics/static/js/course_admin_statistics.js")
        self.template_helper.add_css("/statistics/static/css/statistics.css")

        return (
            self.template_helper.get_custom_renderer(base_renderer_path()).course_admin_statistics(
                course)
        )


def statistics_course_admin_menu_hook(course):
    return "statistics", '<i class="fa fa-bar-chart" aria-hidden="true"></i> Course statistics'
