""" Pages that allow editing of tasks """

import codecs
import collections
import json
import os.path

from common.base import INGIniousConfiguration, id_checker
from frontend.accessible_time import AccessibleTime
from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
from frontend.submission_manager import get_job_manager


class AdminCourseEditTask(object):

    """ Edit a task """

    def GET(self, courseid, taskid):
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")
        course = FrontendCourse(courseid)
        try:
            task_data = json.load(codecs.open(os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid + ".task"), "r", 'utf-8'), object_pairs_hook=collections.OrderedDict)
        except:
            task_data = {}
        environments = get_job_manager().get_container_names()
        return renderer.admin_course_edit_task(course, taskid, task_data, environments, json.dumps(task_data.get('problems', {})), AccessibleTime)
