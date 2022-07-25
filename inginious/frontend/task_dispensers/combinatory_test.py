import json

from collections import OrderedDict
from random import Random
from inginious.frontend.task_dispensers import TaskDispenser
from inginious.frontend.task_dispensers.util import SectionsList, check_toc, SectionConfigItem


class CombinatoryTest(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data, database, course_id):
        self._task_list_func = task_list_func
        self._data = SectionsList(dispenser_data)
        self._database = database
        self._course_id = course_id

    @classmethod
    def get_id(cls):
        return "combinatory_test"

    @classmethod
    def get_name(cls, language):
        return _("Combinatory test")

    def get_course_grade(self, username):
        """ Returns the grade of a user for the current course"""
        task_list = self.get_user_task_list([username])[username]
        tasks_data = {taskid: {"succeeded": False, "grade": 0.0} for taskid in task_list}
        user_tasks = self._database.user_tasks.find({"username": username, "courseid": self._course_id, "taskid": {"$in": task_list}})
        tasks_score = [0.0, 0.0]

        for taskid in task_list:
            tasks_score[1] += self.get_weight(taskid)

        for user_task in user_tasks:
            tasks_data[user_task["taskid"]]["succeeded"] = user_task["succeeded"]
            tasks_data[user_task["taskid"]]["grade"] = user_task["grade"]

            weighted_score = user_task["grade"]*self.get_weight(user_task["taskid"])
            tasks_score[0] += weighted_score

        course_grade = round(tasks_score[0]/tasks_score[1]) if tasks_score[1] > 0 else 0
        return course_grade

    def _get_value_rec(self,taskid,structure,key):
        """
            Returns the value of key for the taskid in the structure if any or None

            The structure can have mutliples sections_list that countains either sections_list or one tasks_list
            The key should be inside one of the tasks_list
        """
        if "sections_list" in structure:
            for section in structure["sections_list"]:
                weight = self._get_value_rec(taskid,section, key)
                if weight is not None:
                    return weight
        elif "tasks_list" in structure:
            if taskid in structure["tasks_list"]:
                return structure[key].get(taskid, None)
        return None

    def get_weight(self, taskid):
        """ Returns the weight of taskid """
        try:
            struct = self._data.to_structure()
            for elem in struct:
                value = self._get_value_rec(taskid,elem,"weights")
                if value is not None:
                    return value
            return 1
        except:
            return 1

    def get_dispenser_data(self):
        return ""

    def render_edit(self, template_helper, course, task_data):
        """ Returns the formatted task list edition form """
        config_fields = {
            "amount": SectionConfigItem(_("Amount of tasks to be displayed"), "number", 0)
        }
        return template_helper.render("course_admin/task_dispensers/combinatory_test.html", course=course,
                                      course_structure=self._data, tasks=task_data, config_fields=config_fields)

    def render(self, template_helper, course, tasks_data, tag_list):
        """ Returns the formatted task list"""
        return template_helper.render("task_dispensers/toc.html", course=course, tasks=self._task_list_func(),
                                      tasks_data=tasks_data, tag_filter_list=tag_list, sections=self._data)

    @classmethod
    def check_dispenser_data(cls, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        new_toc = json.loads(dispenser_data)
        for section in new_toc:
            config = section.setdefault("config", {})
            config["amount"] = int(config.get("amount", 0))
        valid, errors = check_toc(new_toc)
        return new_toc if valid else None, errors

    def get_user_task_list(self, usernames):
        """ Returns a dictionary with username as key and the user task list as value """
        tasks = self._task_list_func()
        result = {username: [] for username in usernames}
        for section in self._data:
            task_list = section.get_tasks()
            task_list = [taskid for taskid in task_list if
                         taskid in tasks and tasks[taskid].get_accessible_time().after_start()]
            amount_questions = int(section.get_config().get("amount", 0))
            for username in usernames:
                rand = Random("{}#{}#{}".format(username, section.get_id(), section.get_title()))
                random_order_choices = list(task_list)
                rand.shuffle(random_order_choices)
                result[username] += random_order_choices[0:amount_questions]
        return result

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        tasks = self._task_list_func()
        return OrderedDict([(taskid, tasks[taskid]) for taskid in self._data.get_tasks() if taskid in tasks])

    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        tasks_id = self._data.get_tasks()
        if taskid in tasks_id:
            return tasks_id.index(taskid)
        else:
            return len(tasks_id)