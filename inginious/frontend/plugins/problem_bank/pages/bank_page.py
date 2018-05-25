import os

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.plugins.problem_bank.constants import _REACT_BUILD_FOLDER, _REACT_BASE_URL

_BASE_RENDERER_PATH = 'frontend/plugins/problem_bank'


class BankPage(INGIniousAdminPage):
    def _list_files_recursive(self, folder):
        return [os.path.relpath(os.path.join(root, name), folder) for root, _, files in os.walk(folder) for name in files]

    def _set_up_compiled_resources(self, build_folder, base_url):
        if not base_url.endswith('/'):
            base_url += '/'

        css_base_folder = 'static/css'
        css_local_folder = os.path.join(build_folder, css_base_folder)
        css_files = [name for name in self._list_files_recursive(css_local_folder) if name.endswith('.css')]

        for file in css_files:
            self.template_helper.add_css(base_url + 'static/css/' + file)

        js_base_folder = 'static/js'
        js_local_folder = os.path.join(build_folder, js_base_folder)
        js_files = [name for name in self._list_files_recursive(js_local_folder) if name.endswith('.js')]

        for file in js_files:
            self.template_helper.add_javascript(base_url + 'static/js/' + file)

    def GET_AUTH(self, course_id):
        self._set_up_compiled_resources(_REACT_BUILD_FOLDER, _REACT_BASE_URL)
        self.get_course_and_check_rights(course_id, None, False)

        return (
            self.template_helper.get_custom_renderer(_BASE_RENDERER_PATH).index()
        )
