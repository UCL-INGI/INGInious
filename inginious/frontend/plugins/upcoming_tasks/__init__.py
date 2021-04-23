# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
#

""" A plugin that allow students to see their futur work in a single place for all their courses """
import os
from collections import OrderedDict
from datetime import datetime, timedelta
import flask
from flask import send_from_directory

from inginious.frontend.pages.utils import INGIniousPage, INGIniousAuthPage

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))

def menu(template_helper):
    """ Displays the link to the board on the main page, if the plugin is activated """
    return template_helper.render("main_menu.html", template_folder=PATH_TO_PLUGIN + '/templates/')

class StaticMockPage(INGIniousPage):
    """ MockPage based on auto-evaluation plugin structure """

    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

    def POST(self, path):
        return self.GET(path)


class UpComingTasksBoard(INGIniousAuthPage):

    def GET_AUTH(self):
        """ Called when reaching the page """
        time_planner = "unlimited"
        return self.page(time_planner)

    def POST_AUTH(self):
        """ Called when modifying time planner """
        user_input = flask.request.form
        time_planner = user_input.get("time_planner", default="unlimited")
        return self.page(time_planner)

    def time_planner_conversion(self, string_time_planner):
        """ Used to convert the time_planner options into int value """
        if string_time_planner in ["7", "14", "30"]:
            return int(string_time_planner)
        return 100000

    def page(self, time_planner):
        """ General main method called for GET and POST """
        username = self.user_manager.session_username()
        all_courses = self.course_factory.get_all_courses()
        time_planner = self.time_planner_conversion(time_planner)

        # Get the courses id
        open_courses = {courseid: course for courseid, course in all_courses.items()
                        if self.user_manager.course_is_open_to_user(course, username, False) and
                        self.user_manager.course_is_user_registered(course, username)}
        open_courses = OrderedDict(sorted(iter(open_courses.items()), key=lambda x: x[1].get_name(self.user_manager.session_language())))

        # Get last submissions for left panel
        last_submissions = self.submission_manager.get_user_last_submissions(5, {"courseid": {"$in": list(open_courses.keys())}})
        except_free_last_submissions = []
        for submission in last_submissions:
            try:
                submission["task"] = open_courses[submission['courseid']].get_task(submission['taskid'])
                except_free_last_submissions.append(submission)
            except:
                pass

        # Get the courses tasks, remove finished ones and courses that have no available unfinished tasks with upcoming deadline in range
        tasks_data = {}
        succeeded_courses = []
        for courseid, course in open_courses.items():
            tasks = course.get_tasks()
            outdated_tasks = [taskid for taskid, task in tasks.items() if (not task.get_accessible_time().is_open()) or ((task.get_accessible_time().get_soft_end_date()) > (datetime.now()+timedelta(days=time_planner)))]
            new_user_task_list = course.get_task_dispenser().get_user_task_list([username])[username]
            new_user_task_list = [task_id for task_id in new_user_task_list if task_id not in outdated_tasks]
            tasks_data[courseid] = {taskid: {"succeeded": False, "grade": 0.0} for taskid in new_user_task_list}
            user_tasks = self.database.user_tasks.find({"username": username, "courseid": course.get_id(), "taskid": {"$in": new_user_task_list}})
            for user_task in user_tasks:
                if not user_task["succeeded"]:
                    tasks_data[courseid][user_task["taskid"]]["succeeded"] = user_task["succeeded"]
                    tasks_data[courseid][user_task["taskid"]]["grade"] = user_task["grade"]
                else:
                    del tasks_data[courseid][user_task["taskid"]]
            # Remove courses with no unfinished available tasks with deadline and lti courses
            if (len(tasks_data[courseid]) == 0) or course.is_lti():
                succeeded_courses.append(courseid)

        # Remove succeeded courses (including lti courses)
        for succeeded_course in succeeded_courses:
            del open_courses[succeeded_course]

        # Sort the courses based on the most urgent task for each course
        open_courses = OrderedDict( sorted(iter(open_courses.items()), key=lambda x: (sort_by_deadline(x[1], tasks_data[x[0]].keys())[0]).get_accessible_time().get_soft_end_date() ))

        return self.template_helper.render("coming_tasks.html",
                                           template_folder=PATH_TO_PLUGIN + "/templates/",
                                           open_courses=open_courses,
                                           tasks_data=tasks_data,
                                           sorting_method=sort_by_deadline,
                                           time_planner=["7", "14", "30", "unlimited"],
                                           submissions=except_free_last_submissions)


def sort_by_deadline(course, user_urgent_task_list):
    """ Given a course (object) and a list of user urgent tasksid,
    returns the list of urgent tasks (objects) for that course ordered based on deadline """
    course_tasks = course.get_tasks()
    course_user_urgent_task_list = list(set(course_tasks).intersection(user_urgent_task_list))
    ordered_tasks = sorted(course_user_urgent_task_list, key=lambda x: course.get_task(x).get_accessible_time().get_soft_end_date())
    return [course_tasks[taskid] for taskid in ordered_tasks]


def init(plugin_manager, _, _2, config):
    """ Init the plugin """
    plugin_manager.add_page('/coming_tasks', UpComingTasksBoard.as_view("upcomingtasksboardpage"))
    plugin_manager.add_page('/plugins/coming_tasks/static/<path:path>', StaticMockPage.as_view("upcomingtasksstaticmockpage"))
    plugin_manager.add_hook('main_menu', menu)
