""" A course class with some modification for users """

from collections import OrderedDict

from common.courses import Course
from frontend.accessible_time import AccessibleTime
from frontend.custom.tasks import FrontendTask


class FrontendCourse(Course):

    """ A course with some modification for users """

    _task_class = FrontendTask

    def __init__(self, courseid):
        Course.__init__(self, courseid)

        if self._content.get('nofrontend', False):
            raise Exception("That course is not allowed to be displayed directly in the frontend")

        if "name" in self._content and "admins" in self._content and isinstance(self._content["admins"], list):
            self._name = self._content['name']
            self._admins = self._content['admins']
            self._accessible = AccessibleTime(self._content.get("accessible", None))
        else:
            raise Exception("Course has an invalid json description: " + courseid)

    def get_name(self):
        """ Return the name of this course """
        return self._name

    def get_admins(self):
        """ Return a list containing the ids of this course """
        return self._admins

    def is_open(self):
        """ Return true if the course is open to students """
        return self._accessible.is_open()

    def get_user_completion_percentage(self):
        """ Returns the percentage (integer) of completion of this course by the current user """
        import frontend.user as User  # insert here to avoid initialisation of session
        count = len(self.get_tasks())  # already in cache
        if count == 0:
            return 0

        cache = User.get_data().get_course_data(self.get_id())
        if cache is None:
            return 0
        return int(cache["task_succeeded"] * 100 / count)

    def get_user_last_submissions(self, limit=5):
        """ Returns a given number (default 5) of submissions of task from this course """
        from frontend.submission_manager import get_user_last_submissions as extern_get_user_last_submissions
        task_ids = []
        for task_id in self.get_tasks():
            task_ids.append(task_id)
        return extern_get_user_last_submissions({"courseid": self.get_id(), "taskid": {"$in": task_ids}}, limit)

    def get_tasks(self):
        return OrderedDict(sorted(Course.get_tasks(self).items(), key=lambda t: t[1].get_order()))
