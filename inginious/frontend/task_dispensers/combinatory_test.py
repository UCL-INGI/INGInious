import json

from collections import OrderedDict
from random import Random
from inginious.frontend.task_dispensers import TaskDispenser
from inginious.frontend.task_dispensers.util import SectionsList, check_toc, parse_tasks_config, check_task_config,\
    SectionConfigItem
from inginious.frontend.accessible_time import AccessibleTime


class CombinatoryTest(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data, database, course_id):
        # Check dispenser data structure
        dispenser_data = dispenser_data or {"toc": {}, "config": {}}
        if not isinstance(dispenser_data, dict) or "toc" not in dispenser_data or "config" not in dispenser_data:
            raise Exception("Invalid dispenser data structure")

        TaskDispenser.__init__(self, task_list_func, dispenser_data, database, course_id)
        self._data = SectionsList(dispenser_data.get("toc", {}))
        self._task_config = dispenser_data.get("config", {})
        parse_tasks_config(self._task_config)

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

    def get_accessibilities(self, taskids, usernames):
        result = {username: {taskid: AccessibleTime(False) for taskid in taskids} for username in usernames}
        for index, section in enumerate(self._data):
            task_list = [taskid for taskid in section.get_tasks()
                         if AccessibleTime(self._task_config.get(taskid, {}).get("accessible", False)).after_start()]
            amount_questions = int(section.get_config().get("amount", 0))
            for username in usernames:
                rand = Random("{}#{}#{}".format(username, index, section.get_title()))
                random_order_choices = list(task_list.keys())
                rand.shuffle(random_order_choices)
                for taskid in random_order_choices[0:amount_questions]:
                    result[username][taskid] = AccessibleTime(self._task_config.get(taskid, {}).get("accessible", False))

        return result

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

    def get_course_grades(self, usernames):
        """ Returns the grade of a user for the current course"""
        taskids = list(self._task_list_func().keys())
        task_list = self.get_accessibilities(taskids, usernames)
        user_tasks = self._database.user_tasks.find(
            {"username": {"$in": usernames}, "courseid": self._course_id, "taskid": {"$in": taskids}})

        tasks_weight = {taskid: self.get_weight(taskid) for taskid in taskids}
        tasks_scores = {username: [0.0, 0.0] for username in usernames}

        for user_task in user_tasks:
            username = user_task["username"]
            if task_list[username][user_task["taskid"]].after_start():
                weighted_score = user_task["grade"] * tasks_weight[user_task["taskid"]]
                tasks_scores[username][0] += weighted_score
                tasks_scores[username][1] += tasks_weight[user_task["taskid"]]

        return {username: round(tasks_scores[username][0]/tasks_scores[username][1])
                if tasks_scores[username][1] > 0 else 0 for username in usernames}

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
            valid, errors = check_task_config(new_toc.get("config", {}))
        return new_toc if valid else None, errors

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        tasks = self._task_list_func()
        return OrderedDict([(taskid, tasks[taskid]) for taskid in self._data.get_tasks() if taskid in tasks])
