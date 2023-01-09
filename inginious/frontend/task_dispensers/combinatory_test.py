import json

from collections import OrderedDict
from random import Random
from inginious.frontend.task_dispensers import TaskDispenser
from inginious.frontend.task_dispensers.util import SectionsList, check_toc, parse_tasks_config, SectionConfigItem, get_course_grade_weighted_sum
from inginious.frontend.accessible_time import AccessibleTime


class CombinatoryTest(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data, database, course_id):
        self._task_list_func = task_list_func
        self._data = SectionsList(dispenser_data.get("toc", {}))
        self._task_config = dispenser_data.get("config", {})
        parse_tasks_config(self._task_config)
        self._database = database
        self._course_id = course_id

    @classmethod
    def get_id(cls):
        return "combinatory_test"

    @classmethod
    def get_name(cls, language):
        return _("Combinatory test")

    def get_weight(self, taskid):
        """ Returns the weight of taskid """
        return self._task_config.get(taskid, {}).get("weight", 1)

    def get_no_stored_submissions(self, taskid):
        """Returns the maximum stored submission specified by the administrator"""
        return self._task_config.get(taskid, {}).get("no_stored_submissions", 0)

    def get_evaluation_mode(self, taskid):
        """Returns the evaluation mode specified by the administrator"""
        return self._task_config.get(taskid, {}).get("evaluation_mode", "best")

    def get_submission_limit(self, taskid):
        """ Returns the submission limits et for the task"""
        return self._task_config.get(taskid, {}).get("submission_limit",  {"amount": -1, "period": -1})

    def get_group_submission(self, taskid):
        """ Indicates if the task submission mode is per groups """
        return self._task_config.get(taskid, {}).get("group_submission", False)

    def get_accessibility(self, taskid, username):
        """  Get the accessible time of this task """
        toc_accessibility = AccessibleTime(self._task_config.get(taskid, {}).get("accessible", False))

        # TODO: kept as in previous code, should refactor the way accessibility is computed for a list of users
        tasks = self._task_list_func()
        result = {username: [] for username in [username]}
        for index, section in enumerate(self._data):
            task_list = section.get_tasks()
            task_list = [taskid for taskid in task_list if taskid in tasks]
            amount_questions = int(section.get_config().get("amount", 0))
            for username in [username]:
                rand = Random("{}#{}#{}".format(username, index, section.get_title()))
                random_order_choices = list(task_list)
                rand.shuffle(random_order_choices)
                result[username] += random_order_choices[0:amount_questions]

        return toc_accessibility if taskid in result[username] else AccessibleTime(False)

    def get_deadline(self, taskid, username):
        """ Returns a string containing the deadline for this task """
        accessible_time = self.get_accessibility(taskid, username)
        if accessible_time.is_always_accessible():
            return _("No deadline")
        elif accessible_time.is_never_accessible():
            return _("It's too late")
        else:
            # Prefer to show the soft deadline rather than the hard one
            return accessible_time.get_soft_end_date().strftime("%d/%m/%Y %H:%M:%S")

    def get_categories(self, taskid):
        """Returns the categories specified for the taskid by the administrator"""
        return self._task_config.get(taskid, {}).get("categories", [])

    def get_all_categories(self):
        """Returns the categories specified by the administrator"""
        tasks = self._data.get_tasks()
        all_categories = []
        for task in tasks:
            try:
                struct = self._data.to_structure()
                for elem in struct:
                    categories = self._data.get_value_rec(task,elem,"categories")
                    if categories is not None:
                        all_categories += categories
            except:
                return all_categories
        return all_categories

    def get_course_grade(self, username):
        """ Returns the grade of a user for the current course"""
        task_list = self.get_user_task_list([username])[username]
        user_tasks = self._database.user_tasks.find({"username": username, "courseid": self._course_id, "taskid": {"$in": task_list}})
        return get_course_grade_weighted_sum(user_tasks, task_list, self.get_weight)

    def get_dispenser_data(self):
        """ Returns the task dispenser data structure """
        return self._data

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

    def check_dispenser_data(self, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        new_toc = json.loads(dispenser_data)
        for section in new_toc.get("toc", {}):
            config = section.setdefault("config", {})
            config["amount"] = int(config.get("amount", 0))
        valid, errors = check_toc(new_toc.get("toc", {}))
        if valid:
            try:
                parse_tasks_config(new_toc.get("config", {}))
            except Exception as ex:
                valid, errors = False, str(ex)
        return new_toc if valid else None, errors

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