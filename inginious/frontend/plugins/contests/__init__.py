# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" An algorithm contest plugin for INGInious. Based on the same principles than contests like ACM-ICPC. """

import copy
from collections import OrderedDict
from datetime import datetime, timedelta

import pymongo
import flask

from werkzeug.exceptions import NotFound
from inginious.frontend.accessible_time import AccessibleTime
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.pages.utils import INGIniousAuthPage


def add_admin_menu(course): # pylint: disable=unused-argument
    """ Add a menu for the contest settings in the administration """
    return ('contest', '<i class="fa fa-trophy fa-fw"></i>&nbsp; Contest')


def task_accessibility(course, task, default): # pylint: disable=unused-argument
    contest_data = get_contest_data(course)
    if contest_data['enabled']:
        return AccessibleTime(contest_data['start'] + '/')
    else:
        return default


def additional_headers():
    """ Additional HTML headers """
    return '<link href="' + flask.request.url_root \
           + '/static/plugins/contests/scoreboard.css" rel="stylesheet">' \
             '<script src="' + flask.request.url_root + '/static/plugins/contests/jquery.countdown.min.js"></script>' \
             '<script src="' + flask.request.url_root + '/static/plugins/contests/contests.js"></script>'


def get_contest_data(course):
    """ Returns the settings of the contest for this course """
    return course.get_descriptor().get('contest_settings', {"enabled": False,
                                                            "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                            "end": (datetime.now() + timedelta(hours=1)).strftime(
                                                                "%Y-%m-%d %H:%M:%S"),
                                                            "blackout": 0,
                                                            "penalty": 20})


def course_menu(course, template_helper):
    """ Displays some informations about the contest on the course page"""
    contest_data = get_contest_data(course)
    if contest_data['enabled']:
        start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
        blackout = end - timedelta(hours=contest_data['blackout'])
        return template_helper.render("course_menu.html", template_folder="frontend/plugins/contests",
                                      course=course, start=start, end=end, blackout=blackout)
    else:
        return None


class ContestScoreboard(INGIniousAuthPage):
    """ Displays the scoreboard of the contest """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        course = self.course_factory.get_course(courseid)
        contest_data = get_contest_data(course)
        if not contest_data['enabled']:
            raise NotFound()
        start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
        blackout = end - timedelta(hours=contest_data['blackout'])

        users = self.user_manager.get_course_registered_users(course)
        tasks = list(course.get_tasks().keys())

        db_results = self.database.submissions.find({
            "username": {"$in": users},
            "courseid": courseid,
            "submitted_on": {"$gte": start, "$lt": blackout},
            "status": "done"},
            {"username": True, "_id": False, "taskid": True, "result": True, "submitted_on": True}).sort([("submitted_on", pymongo.ASCENDING)])

        task_status = {taskid: {"status": "NA", "tries": 0} for taskid in tasks}
        results = {username: {"name": self.user_manager.get_user_realname(username), "tasks": copy.deepcopy(task_status)} for username in users}
        activity = []

        # Compute stats for each submission
        task_succeeded = {taskid: False for taskid in tasks}
        for submission in db_results:
            for username in submission["username"]:
                if submission['taskid'] not in tasks:
                    continue
                if username not in users:
                    continue
                status = results[username]["tasks"][submission['taskid']]
                if status["status"] == "AC" or status["status"] == "ACF":
                    continue
                else:
                    if submission['result'] == "success":
                        if not task_succeeded[submission['taskid']]:
                            status["status"] = "ACF"
                            task_succeeded[submission['taskid']] = True
                        else:
                            status["status"] = "AC"
                        status["tries"] += 1
                        status["time"] = submission['submitted_on']
                        status["score"] = (submission['submitted_on']
                                           + timedelta(minutes=contest_data["penalty"]*(status["tries"] - 1))
                                           - start).total_seconds() / 60
                    elif submission['result'] == "failed" or submission['result'] == "killed":
                        status["status"] = "WA"
                        status["tries"] += 1
                    elif submission['result'] == "timeout":
                        status["status"] = "TLE"
                        status["tries"] += 1
                    else:  # other internal error
                        continue
                    activity.append({"user": results[username]["name"],
                                     "when": submission['submitted_on'],
                                     "result": (status["status"] == 'AC' or status["status"] == 'ACF'),
                                     "taskid": submission['taskid']})
        activity.reverse()
        # Compute current score
        for user in results:
            score = [0, 0]
            for data in list(results[user]["tasks"].values()):
                if "score" in data:
                    score[0] += 1
                    score[1] += data["score"]
            results[user]["score"] = tuple(score)

        # Sort everybody
        results = OrderedDict(sorted(list(results.items()), key=lambda t: (-t[1]["score"][0], t[1]["score"][1])))

        # Compute ranking
        old = None
        current_rank = 0
        for cid, user in enumerate(results.keys()):
            if results[user]["score"] != old:
                old = results[user]["score"]
                current_rank = cid + 1
                results[user]["rank"] = current_rank
                results[user]["displayed_rank"] = str(current_rank)
            else:
                results[user]["rank"] = current_rank
                results[user]["displayed_rank"] = ""

        return self.template_helper.render("scoreboard.html", template_folder="frontend/plugins/contests",
                                           course=course, start=start, end=end, blackout=blackout, tasks=tasks,
                                           results=results, activity=activity)


class ContestAdmin(INGIniousAdminPage):
    """ Contest settings for a course """

    def save_contest_data(self, course, contest_data):
        """ Saves updated contest data for the course """
        course_content = self.course_factory.get_course_descriptor_content(course.get_id())
        course_content["contest_settings"] = contest_data
        self.course_factory.update_course_descriptor_content(course.get_id(), course_content)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request: simply display the form """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contest_data = get_contest_data(course)
        return self.template_helper.render("admin.html", template_folder="frontend/plugins/contests", course=course,
                                           data=contest_data, errors=None, saved=False)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ POST request: update the settings """
        course, __ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        contest_data = get_contest_data(course)

        new_data = flask.request.form
        errors = []
        try:
            contest_data['enabled'] = new_data.get('enabled', '0') == '1'
            contest_data['start'] = new_data["start"]
            contest_data['end'] = new_data["end"]

            try:
                start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
            except:
                errors.append('Invalid start date')

            try:
                end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
            except:
                errors.append('Invalid end date')

            if len(errors) == 0:
                if start >= end:
                    errors.append('Start date should be before end date')

            try:
                contest_data['blackout'] = int(new_data["blackout"])
                if contest_data['blackout'] < 0:
                    errors.append('Invalid number of hours for the blackout: should be greater than 0')
            except:
                errors.append('Invalid number of hours for the blackout')

            try:
                contest_data['penalty'] = int(new_data["penalty"])
                if contest_data['penalty'] < 0:
                    errors.append('Invalid number of minutes for the penalty: should be greater than 0')
            except:
                errors.append('Invalid number of minutes for the penalty')
        except:
            errors.append('User returned an invalid form')

        if len(errors) == 0:
            self.save_contest_data(course, contest_data)
            return self.template_helper.render("admin.html", template_folder="frontend/plugins/contests", course=course,
                                               data=contest_data, errors=None, saved=True)
        else:
            return self.template_helper.render("admin.html", template_folder="frontend/plugins/contests", course=course,
                                               data=contest_data, errors=errors, saved=False)


def init(plugin_manager, course_factory, client, config):  # pylint: disable=unused-argument
    """
        Init the contest plugin.
        Available configuration:
        ::

            {
                "plugin_module": "inginious.frontend.plugins.contests"
            }
    """

    plugin_manager.add_page('/contest/<courseid>', ContestScoreboard.as_view('contestscoreboard'))
    plugin_manager.add_page('/admin/<courseid>/contest', ContestAdmin.as_view('contestadmin'))
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    plugin_manager.add_hook('task_accessibility', task_accessibility)
    plugin_manager.add_hook('header_html', additional_headers)
    plugin_manager.add_hook('course_menu', course_menu)
