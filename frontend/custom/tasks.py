""" Classes modifying basic tasks, problems and boxes classes """
from common.parsable_text import ParsableText
from frontend.accessible_time import AccessibleTime
from frontend.custom.task_problems import DisplayableCodeProblem, DisplayableCodeSingleLineProblem, DisplayableMatchProblem, DisplayableMultipleChoiceProblem
import common.tasks


class FrontendTask(common.tasks.Task):

    """ A task that stores additionnal context informations """

    # Redefine _problem_types with displayable ones
    _problem_types = {"code": DisplayableCodeProblem, "code-single-line": DisplayableCodeSingleLineProblem, "multiple-choice": DisplayableMultipleChoiceProblem, "match": DisplayableMatchProblem}

    def __init__(self, course, taskid):
        common.tasks.Task.__init__(self, course, taskid)

        self._name = self._data.get('name', 'Task {}'.format(taskid))

        self._context = ParsableText(self._data.get('context', ""), "HTML" if self._data.get("contextIsHTML", False) else "rst")

        # Authors
        if isinstance(self._data.get('author'), basestring):  # verify if author is a string
            self._author = [self._data['author']]
        elif isinstance(self._data.get('author'), list):  # verify if author is a list
            for author in self._data['author']:
                if not isinstance(author, basestring):  # authors must be strings
                    raise Exception("This task has an invalid author")
            self._author = self._data['author']
        else:
            self._author = []

        # _accessible
        self._accessible = AccessibleTime(self._data.get("accessible", None))

        # Order
        self._order = int(self._data.get('order', -1))

    def get_name(self):
        """ Returns the name of this task """
        return self._name

    def get_context(self):
        """ Get the context(description) of this task """
        return self._context

    def get_authors(self):
        """ Return the list of this task's authors """
        return self._author

    def get_order(self):
        """ Get the position of this task in the course """
        return self._order

    def is_open(self):
        """ Returns if the task is open to students """
        return self._accessible.is_open()

    def get_user_status(self):
        """ Returns "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet """
        import frontend.user as User  # insert here to avoid initialisation of session
        task_cache = User.get_data().get_task_data(self.get_course_id(), self.get_id())
        if task_cache is None:
            return "notviewed"
        if task_cache["tried"] == 0:
            return "notattempted"
        return "succeeded" if task_cache["succeeded"] else "failed"
