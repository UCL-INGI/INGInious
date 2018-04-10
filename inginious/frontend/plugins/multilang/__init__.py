import os

from inginious.common.tasks_problems import CodeProblem
from inginious.frontend.task_problems import DisplayableCodeProblem

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))

class CodeMultipleLanguagesProblem(CodeProblem):
    def __init__(self, task, problemid, content, translations=None):
        CodeProblem.__init__(self, task, problemid, content, translations)

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
        return template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, "templates"), False)

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("Code multiple languages")

    @classmethod
    def show_editbox(cls, template_helper, key):
        renderer = DisplayableCodeMultipleLanguagesProblem.get_renderer(template_helper)
        return renderer.multilang_edit(key, cls._available_languages)


def init(plugin_manager, course_factory, client, plugin_config):
    course_factory.get_task_factory().add_problem_type(DisplayableCodeMultipleLanguagesProblem)
