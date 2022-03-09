from abc import ABCMeta, abstractmethod

class TaskDispenser(metaclass=ABCMeta):
    def __init__(self, task_list_func, dispenser_data, database, course_id):
        """
        Instantiate a new TaskDispenser
        :param task_list_func: A function returning the list of available course tasks from the task factory
        :param dispenser_data: The dispenser data structure/configuration
        :param database: The MongoDB database
        :param course_id: A String that is the id of the course
        """
        pass

    @classmethod
    @abstractmethod
    def get_id(cls):
        """ Returns the task dispenser id """
        pass

    @classmethod
    @abstractmethod
    def get_name(cls, language):

        """ Returns the localized task dispenser name """
        pass

    @abstractmethod
    def get_dispenser_data(self):
        """ Returns the task dispenser data structure """
        pass

    @abstractmethod
    def render_edit(self, template_helper, course, task_data):
        """ Returns the formatted task list edition form """
        pass

    @abstractmethod
    def render(self, template_helper, course, tasks_data, tag_list):
        """ Returns the formatted task list"""
        pass

    @classmethod
    @abstractmethod
    def check_dispenser_data(cls, dispenser_data):
        """ Checks the dispenser data as formatted by the form from render_edit function """
        pass

    def filter_accessibility(self, taskid, username):
        """ Returns true if the task is accessible by all students that are not administrator of the course """
        user_task_list = self.get_user_task_list([username])
        return taskid in user_task_list[username]

    @abstractmethod
    def get_user_task_list(self, usernames):
        """
        Returns the user task list that are eligible for grade computation
        :param usernames: List of usernames for which get the user task list
        :return: Returns a dictionary with username as key and the user task list as value
        """

    @abstractmethod
    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        pass

    @abstractmethod
    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        pass