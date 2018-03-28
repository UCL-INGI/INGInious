import os
from inginious.frontend.plugins.utils import create_static_resource_page

_static_folder_path = os.path.join(os.path.dirname(__file__), "static")

def init(plugin_manager, _, _2, _3):
    """ Init the plugin """
    plugin_manager.add_page(r'/plugindemo/static/(.*)', create_static_resource_page(_static_folder_path))
