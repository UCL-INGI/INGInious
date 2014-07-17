""" Modify tasks utilities classes (from modules common.tasks_code_boxes and common.tasks_problems) to include show functions """

from random import shuffle

import web

from common.courses import Course
from common.tasks import Task
from common.tasks_code_boxes import BasicBox, TextBox, InputBox, MultilineBox
from common.tasks_problems import BasicCodeProblem, MultipleChoiceProblem, MatchProblem


# Add show functions to problems' boxes
def basic_box_str(self):
    """ Allow to do use __str__ and __unicode__ functions on all derivatives of BasicBox """
    return self.show(self)
BasicBox.__str__ = basic_box_str
BasicBox.__unicode__ = basic_box_str


def text_box_show(self):
    """ Show TextBox """
    return str(web.template.render('templates/tasks/').box_text(self._content.parse()))
TextBox.show = text_box_show


def input_box_show(self):
    """ Show InputBox """
    return str(web.template.render('templates/tasks/').box_input(self.get_complete_id(), self._input_type, self._max_chars))
InputBox.show = input_box_show


def multiline_box_show(self):
    """ Show MultilineBox """
    return str(web.template.render('templates/tasks/').box_multiline(self.get_complete_id(), self._lines, self._max_chars, self._language))
MultilineBox.show = multiline_box_show

# Add show_input functions to tasks' problems


def basic_code_problem_show_input(self):
    """ Show BasicCodeProblem and derivatives """
    output = ""
    for box in self._boxes:
        output += box.show()
    return output
BasicCodeProblem.show_input = basic_code_problem_show_input


def match_problem_show_input(self):
    """ Show MatchProblem """
    return str(web.template.render('templates/tasks/').match(self.get_id()))
MatchProblem.show_input = match_problem_show_input


def mchoice_problem_show_input(self):
    """ Show multiple choice problems """
    choices = []
    limit = self._limit
    if self._multiple:
        # take only the valid choices in the first pass
        for entry in self._choices:
            if entry['valid']:
                choices.append(entry)
                limit = limit - 1
        # take everything else in a second pass
        for entry in self._choices:
            if limit == 0:
                break
            if not entry['valid']:
                choices.append(entry)
                limit = limit - 1
    else:
        # need to have a valid entry
        found_valid = False
        for entry in self._choices:
            if limit == 1 and not found_valid and not entry['valid']:
                continue
            elif limit == 0:
                break
            choices.append(entry)
            limit = limit - 1
            if entry['valid']:
                found_valid = True
    shuffle(choices)
    return str(web.template.render('templates/tasks/').multiplechoice(self.get_id(), self._multiple, choices))
MultipleChoiceProblem.show_input = mchoice_problem_show_input

# Add utilities function to manage submissions from the task class


def get_user_status(self):
    """ Returns "succeeded" if the current user solved this task, "failed" if he failed, and "notattempted" if he did not try it yet """
    import frontend.user as User  # insert here to avoid initialisation of session
    task_cache = User.get_data().get_task_data(self.get_course_id(), self.get_id())
    if task_cache is None:
        return "notviewed"
    if task_cache["tried"] == 0:
        return "notattempted"
    return "succeeded" if task_cache["succeeded"] else "failed"
Task.get_user_status = get_user_status

# Add utilities function to manage submissions from the course class


def get_user_completion_percentage(self):
    """ Returns the percentage (integer) of completion of this course by the current user """
    import frontend.user as User  # insert here to avoid initialisation of session
    count = len(self.get_tasks())  # already in cache
    cache = User.get_data().get_course_data(self.get_id())
    if cache is None:
        return 0
    return int(cache["task_succeeded"] * 100 / count)

Course.get_user_completion_percentage = get_user_completion_percentage


def get_user_last_submissions(self, limit=5):
    """ Returns a given number (default 5) of submissions of task from this course """
    from frontend.submission_manager import get_user_last_submissions as extern_get_user_last_submissions
    task_ids = []
    for task_id in self.get_tasks():
        task_ids.append(task_id)
    return extern_get_user_last_submissions({"courseid": self.get_id(), "taskid": {"$in": task_ids}}, limit)
Course.get_user_last_submissions = get_user_last_submissions
