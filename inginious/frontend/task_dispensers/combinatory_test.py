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

    @classmethod
    def get_id(cls):
        return "combinatory_test"

    @classmethod
    def get_name(cls, language):
        return _("Combinatory test")

    def get_course_grade(self, username, course, user_task_list):
        tasks = course.get_tasks()
        tasks_data = {taskid: {"succeeded": False, "grade": 0.0} for taskid in user_task_list}
        user_tasks = self._database.user_tasks.find({"username": username, "courseid": course.get_id(), "taskid": {"$in": user_task_list}})
        tasks_score = [0.0, 0.0]

        for taskid in user_task_list:
            tasks_score[1] += tasks[taskid].get_grading_weight()

        for user_task in user_tasks:
            tasks_data[user_task["taskid"]]["succeeded"] = user_task["succeeded"]
            tasks_data[user_task["taskid"]]["grade"] = user_task["grade"]

            weighted_score = user_task["grade"]*tasks[user_task["taskid"]].get_grading_weight()
            tasks_score[0] += weighted_score

        course_grade = round(tasks_score[0]/tasks_score[1]) if tasks_score[1] > 0 else 0
        return course_grade

    def get_weight(self, taskid):
        try:
            weights = self._data.to_structure()[0]["weights"]
            if taskid in weights:
                return weights[taskid]
            return 1
        except:
            return 1

    def get_stored_submissions(self,taskid):
        try:
            stored_submissions = self._data.to_structure()[0]["store_submission"]
            if taskid in stored_submissions:
                return stored_submissions[taskid]
            return 0
        except:
            return 0

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