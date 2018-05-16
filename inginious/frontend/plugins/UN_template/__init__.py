import os
from inginious.frontend.plugins.utils import create_static_resource_page

_static_folder_path = os.path.join(os.path.dirname(__file__), "static")


def header(template_helper):
    def hook():
        template_helper.add_javascript("/UN_template/static/js/user_statistics.js")
        template_helper.add_css("/UN_template/static/css/statistics.css")
        return str(template_helper.get_custom_renderer('frontend/plugins/UN_template', layout=False).header("UNCode"))
    return hook;

def init(plugin_manager, course_factory, client, config):
    print("UN_Template")
    plugin_manager.add_page(r'/UN_template/static/(.*)', create_static_resource_page(_static_folder_path))
    plugin_manager.add_hook('UN_header', header(plugin_manager._app.template_helper))
