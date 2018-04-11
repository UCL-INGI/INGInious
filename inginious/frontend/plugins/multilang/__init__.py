import os

from inginious.frontend.plugins.utils import create_static_resource_page
from inginious.common.tasks_problems import CodeProblem
from inginious.frontend.task_problems import DisplayableCodeProblem

path_to_plugin = os.path.abspath(os.path.dirname(__file__))
_static_folder_path = os.path.join(os.path.dirname(__file__), "static")


class CodeMultipleLanguagesProblem(CodeProblem):
    def __init__(self, task, problemid, content, translations=None):
        CodeProblem.__init__(self, task, problemid, content, translations)
        self._languages = content["languages"]

    @classmethod
    def get_type(cls):
        return "code_multiple_languages"


class DisplayableCodeMultipleLanguagesProblem(CodeMultipleLanguagesProblem, DisplayableCodeProblem):
    def __init__(self, task, problemid, content, translations=None):
        CodeMultipleLanguagesProblem.__init__(self, task, problemid, content, translations)

    _available_languages = {
        "java7": "Java 7",
        "java8": "Java 8",
        "python2": "Python 2.7",
        "python3": "Python 3.5",
        "cpp": "C++",
        "cpp11": "C++11",
        "c": "C",
        "c11": "C11"}

    @classmethod
    def get_renderer(cls, template_helper):
        """ Get the renderer for this class problem """
        return template_helper.get_custom_renderer(os.path.join(path_to_plugin, "templates"), False)

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("Code multiple languages")

    @classmethod
    def show_editbox(cls, template_helper, key):
        renderer = DisplayableCodeMultipleLanguagesProblem.get_renderer(template_helper)
        return renderer.multilang_edit(key, cls._available_languages)

    def show_input(self, template_helper, language, seed):
        allowed_languages = {language: self._available_languages[language] for language in self._languages}
        dropdown_id = self.get_id() + "/language"
        custom_input_id = self.get_id() + "/input"

        renderer = DisplayableCodeMultipleLanguagesProblem.get_renderer(template_helper)

        multiple_language_render = str(renderer.multilang(self.get_id(), dropdown_id, allowed_languages, self.get_id(), self.get_type()))
        standard_code_problem_render = super(DisplayableCodeMultipleLanguagesProblem, self).show_input(template_helper, language, seed)
        tools_render = ""#str(renderer.tasks.tools(self.get_id(), "plain", custom_input_id, self.get_type()))

        return multiple_language_render + standard_code_problem_render + tools_render



def init(plugin_manager, course_factory, client, plugin_config):
    plugin_manager.add_page(r'/multilang/static/(.*)', create_static_resource_page(_static_folder_path))
    plugin_manager.add_hook("javascript_header", lambda: "/multilang/static/multilang.js")
    course_factory.get_task_factory().add_problem_type(DisplayableCodeMultipleLanguagesProblem)
