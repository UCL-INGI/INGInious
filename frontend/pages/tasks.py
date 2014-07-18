""" Task page """
import json

import web

from common.tasks_problems import MultipleChoiceProblem
from frontend.base import renderer
from frontend.custom.courses import FrontendCourse
import frontend.submission_manager as submission_manager
import frontend.user as User


class TaskPage(object):

    """ Display a task """

    def GET(self, courseid, taskid):
        """ GET request """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if not course.is_open() and User.get_username() not in course.get_admins():
                    return renderer.course_unavailable()

                task = course.get_task(taskid)
                if not task.is_open() and User.get_username() not in course.get_admins():
                    return renderer.task_unavailable()

                User.get_data().view_task(courseid, taskid)
                return renderer.task(course, task, submission_manager.get_user_submissions(task))
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def POST(self, courseid, taskid):
        """ POST a new submission """
        if User.is_logged_in():
            try:
                course = FrontendCourse(courseid)
                if not course.is_open() and User.get_username() not in course.get_admins():
                    return renderer.course_unavailable()

                task = course.get_task(taskid)
                if not task.is_open() and User.get_username() not in course.get_admins():
                    return renderer.task_unavailable()

                User.get_data().view_task(courseid, taskid)
                userinput = web.input()
                if "@action" in userinput and userinput["@action"] == "submit":
                    # Reparse user input with array for multiple choices
                    need_array = self.list_multiple_multiple_choices(task)
                    userinput = web.input(**dict.fromkeys(need_array, []))
                    if not task.input_is_consistent(userinput):
                        web.header('Content-Type', 'application/json')
                        return json.dumps({"status": "error", "text": "Please answer to all the questions. Your responses were not tested."})
                    del userinput['@action']
                    submissionid = submission_manager.add_job(task, userinput)
                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "ok", "submissionid": str(submissionid)})
                elif "@action" in userinput and userinput["@action"] == "check" and "submissionid" in userinput:
                    if submission_manager.is_done(userinput['submissionid']):
                        web.header('Content-Type', 'application/json')
                        result = submission_manager.get_submission(userinput['submissionid'])
                        return self.submission_to_json(result)
                    else:
                        web.header('Content-Type', 'application/json')
                        return json.dumps({'status': "waiting"})
                elif "@action" in userinput and userinput["@action"] == "load_submission_input" and "submissionid" in userinput:
                    submission = submission_manager.get_submission(userinput["submissionid"])
                    if not submission:
                        raise web.notfound()
                    web.header('Content-Type', 'application/json')
                    return json.dumps({"status": "ok", "input": submission["input"]})
                else:
                    raise web.notfound()
            except:
                if web.config.debug:
                    raise
                else:
                    raise web.notfound()
        else:
            return renderer.index(False)

    def submission_to_json(self, data):
        """ Converts a submission to json (keeps only needed fields) """
        tojson = {'status': data['status'], 'result': data['result'], 'id': str(data["_id"]), 'submitted_on': str(data['submitted_on'])}
        if "text" in data:
            tojson["text"] = data["text"]
        if "problems" in data:
            tojson["problems"] = data["problems"]
        return json.dumps(tojson)

    def list_multiple_multiple_choices(self, task):
        """ List problems in task that expect and array as input """
        output = []
        for problem in task.get_problems():
            if isinstance(problem, MultipleChoiceProblem) and problem.allow_multiple():
                output.append(problem.get_id())
        return output
