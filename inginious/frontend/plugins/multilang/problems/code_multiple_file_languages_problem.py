import os

from inginious.common.tasks_problems import FileProblem
from inginious.frontend.task_problems import DisplayableFileProblem
from .languages import available_languages

path_to_plugin = os.path.abspath(os.path.dirname(__file__))

class CodeFileMultipleLanguagesProblem (FileProblem):
    """Code file problem with multiple languages"""

    def __init__(self, task, problemid, content, translations=None):
        FileProblem.__init__(self, task, problemid, content, translations)
        self._languages = content["languages"]

    @classmethod
    def get_type(cls):
        return "code_file_multiple_languages"

class DisplayableCodeFileMultipleLanguagesProblem(CodeFileMultipleLanguagesProblem, DisplayableFileProblem):
    """ A displayable code file problem with multiple languages """

    def __init__(self, task, problemid, content, translations=None):
        CodeFileMultipleLanguagesProblem.__init__(self, task, problemid, content, translations)

    @classmethod
    def get_renderer(cls, template_helper):
        """ Get the renderer for this class problem """
        return template_helper.get_custom_renderer(os.path.join(path_to_plugin, "templates"), False)

    @classmethod
    def get_type_name(cls, gettext):
        return gettext("code file multiple languages")

    @classmethod
    def show_editbox(cls, template_helper, key):
        renderer = DisplayableCodeFileMultipleLanguagesProblem.get_renderer(template_helper)
        return renderer.file_multilang_edit(key, available_languages())

    def show_input(self, template_helper, language, seed):
        allowed_languages = {language: available_languages()[language] for language in self._languages}
        dropdown_id = self.get_id() + "/language"
        custom_input_id = self.get_id() + "/input"

        renderer = DisplayableCodeFileMultipleLanguagesProblem.get_renderer(template_helper)

        multiple_language_render = str(renderer.multilang(self.get_id(), dropdown_id, allowed_languages, self.get_id(), self.get_type()))
        standard_code_problem_render = super(DisplayableCodeFileMultipleLanguagesProblem, self).show_input(template_helper, language, seed)
        tools_render = str(renderer.tools(self.get_id(), "plain", custom_input_id, self.get_type(), "python_tutor_url", "linter_url"))

        return multiple_language_render + standard_code_problem_render + tools_render
