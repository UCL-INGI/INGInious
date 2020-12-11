import json

from collections import OrderedDict
from random import Random
from inginious.frontend.task_dispensers import TaskDispenser
from inginious.frontend.task_dispensers.util import SectionsList, check_toc, SectionConfigItem


class CombinatoryTest(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data):
        self._task_list_func = task_list_func
        self._data = SectionsList(dispenser_data)

    @classmethod
    def get_id(cls):
        return "combinatory_test"

    @classmethod
    def get_name(cls, language):
        return _("Combinatory test")

    def get_dispenser_data(self):
        return ""

    def render_edit(self, template_helper, course, task_data):
        """ Returns the formatted task list edition form """
        config_fields = {
            "amount": SectionConfigItem(_("Amount of tasks to be displayed"), "number")
        }
        return template_helper.get_renderer(with_layout=False).course_admin.task_dispensers.combinatory_test(
            course, self._data, task_data, config_fields)

    def render(self, template_helper, course, tasks_data, tag_list):
        """ Returns the formatted task list"""
        return template_helper.get_renderer(with_layout=False).task_dispensers.toc(
            course, self._task_list_func(), tasks_data, tag_list, self._data)

    @classmethod
    def check_dispenser_data(cls, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        new_toc = json.loads(dispenser_data)
        valid, errors = check_toc(new_toc)
        for section in new_toc:
            config = section.setdefault("config", {})
            config["amount"] = int(config.get("amount", 0))
        return new_toc if valid else None, errors

    def filter_accessibility(self, taskid, username):
        """ Returns true if the task is accessible by all students that are not administrator of the course """
        for section in self._data:
            task_list = section.get_tasks()
            if taskid in task_list:
                amount_questions = int(section.get_config().get("amount", 0))
                rand = Random("{}#{}#{}".format(username, section.get_id(), section.get_title()))
                random_order_choices = list(task_list)
                rand.shuffle(random_order_choices)
                return taskid in random_order_choices[0:amount_questions]
        return False

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        return OrderedDict(sorted(list(self._task_list_func().items()), key=lambda t: (self.get_task_order(t[1].get_id()), t[1].get_id())))

    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        tasks_id = self._data.get_tasks()
        if taskid in tasks_id:
            return tasks_id.index(taskid)
        else:
            return len(tasks_id)