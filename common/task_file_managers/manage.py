import os.path

from common.base import get_tasks_directory
from common.task_file_managers.yaml_manager import TaskYAMLFileManager

_task_file_managers = [TaskYAMLFileManager]


def get_readable_tasks(courseid):
    """ Returns the list of all available tasks in a course """
    tasks = [
        task for task in os.listdir(os.path.join(get_tasks_directory(), courseid))
        if os.path.isdir(os.path.join(get_tasks_directory(), courseid, task))
        and _task_file_exists(os.path.join(get_tasks_directory(), courseid, task))]
    return tasks


def _task_file_exists(directory):
    """ Returns true if a task file exists in this directory """
    for filename in ["task.{}".format(ext) for ext in get_available_task_file_managers().keys()]:
        if os.path.isfile(os.path.join(directory, filename)):
            return True
    return False


def get_task_file_manager(courseid, taskid):
    """ Returns the appropriate task file manager for this task """
    for ext, subclass in get_available_task_file_managers().iteritems():
        if os.path.isfile(os.path.join(get_tasks_directory(), courseid, taskid, "task.{}".format(ext))):
            return subclass(courseid, taskid)
    return None


def delete_all_possible_task_files(courseid, taskid):
    """ Deletes all possibles task files in directory, to allow to change the format """
    for ext in get_available_task_file_managers().keys():
        try:
            os.remove(os.path.join(get_tasks_directory(), courseid, taskid, "task.{}".format(ext)))
        except:
            pass


def add_custom_task_file_manager(task_file_manager):
    """ Add a custom task file manager """
    _task_file_managers.append(task_file_manager)


def get_available_task_file_managers():
    """ Get a dict with ext:class pairs """
    return {f.get_ext(): f for f in _task_file_managers}
