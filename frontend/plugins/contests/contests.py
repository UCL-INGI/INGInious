# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" An algorithm contest plugin for INGInious. Based on the same principles than contests like ACM-ICPC. """

import codecs
from collections import OrderedDict
import copy
from datetime import datetime, timedelta
import json

import pymongo
import web

from frontend.base import get_template_renderer, get_database
from frontend.custom.courses import FrontendCourse
from frontend.pages.course_admin.utils import get_course_and_check_rights
from frontend.user_data import UserData


def add_admin_menu(course):
    """ Add a menu for the contest settings in the administration """
    return ('contest', '<span class="glyphicon glyphicon-tower"></span> Contest plugin')


def modify_task_data(course, taskid, data):
    """ Modify the availability of tasks during contests """
    contest_data = get_contest_data(course)
    if contest_data['enabled']:
        data['accessible'] = contest_data['start'] + '/'


def additional_headers():
    """ Additional HTML headers """
    return """
        <link href="/static/plugins/contests/scoreboard.css" rel="stylesheet">
        <script src="/static/plugins/contests/jquery.countdown.min.js"></script>
        <script src="/static/plugins/contests/contests.js"></script>
    """


def get_contest_data(course):
    """ Returns the settings of the contest for this course """
    return course.get_original_content().get('contest_settings', {"enabled": False,
                                                                  "start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                  "end": (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
                                                                  "blackout": 0,
                                                                  "penalty": 20})


def save_contest_data(course, contest_data):
    """ Saves updated contest data for the course """
    course_content = course.get_original_content()
    course_content["contest_settings"] = contest_data
    with codecs.open(course.get_course_descriptor_path(course.get_id()), "w", 'utf-8') as course_file:
        course_file.write(json.dumps(course_content, sort_keys=False, indent=4, separators=(',', ': ')))


def course_menu(course):
    """ Displays some informations about the contest on the course page"""
    contest_data = get_contest_data(course)
    if contest_data['enabled']:
        start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
        blackout = end - timedelta(hours=contest_data['blackout'])
        return str(get_template_renderer('frontend/plugins/contests').course_menu(course, start, end, blackout))
    else:
        return None


class ContestScoreboard(object):

    """ Displays the scoreboard of the contest """

    def GET(self, courseid):
        # try:
        course = FrontendCourse(courseid)
        contest_data = get_contest_data(course)
        if not contest_data['enabled']:
            raise web.notfound()
        start = datetime.strptime(contest_data['start'], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(contest_data['end'], "%Y-%m-%d %H:%M:%S")
        blackout = end - timedelta(hours=contest_data['blackout'])

        users = course.get_registered_users(True)
        tasks = course.get_tasks().keys()

        db_results = get_database().submissions.find({
            "username": {"$in": users},
            "courseid": courseid,
            "submitted_on": {"$gte": start, "$lt": blackout},
            "status": "done"},
            {"username": True, "_id": False, "taskid": True, "result": True, "submitted_on": True}).sort([("submitted_on", pymongo.ASCENDING)])

        task_status = {taskid: {"status": "NA", "tries": 0} for taskid in tasks}
        results = {username: {"name": UserData(username).get_data()['realname'], "tasks": copy.deepcopy(task_status)} for username in users}
        activity = []

        # Compute stats for each submission
        task_succeeded = {taskid: False for taskid in tasks}
        for submission in db_results:
            if submission['taskid'] not in tasks:
                continue
            if submission['username'] not in users:
                continue
            status = results[submission['username']]["tasks"][submission['taskid']]
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
                    status["score"] = ((submission['submitted_on'] + (timedelta(minutes=contest_data["penalty"]) * (status["tries"] - 1))) - start).total_seconds() / 60
                elif submission['result'] == "failed":
                    status["status"] = "WA"
                    status["tries"] += 1
                elif submission['result'] == "timeout":
                    status["status"] = "TLE"
                    status["tries"] += 1
                else:  # other internal error
                    continue
                activity.append({"user": results[submission['username']]["name"],
                                 "when": submission['submitted_on'],
                                 "result": (status["status"] == 'AC' or status["status"] == 'ACF'),
                                 "taskid": submission['taskid']})
        activity.reverse()
        # Compute current score
        for user in results:
            score = [0, 0]
            for data in results[user]["tasks"].values():
                if "score" in data:
                    score[0] += 1
                    score[1] += data["score"]
            results[user]["score"] = tuple(score)

        # Sort everybody
        results = OrderedDict(sorted(results.items(), key=lambda t: (-t[1]["score"][0], t[1]["score"][1])))

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

        return get_template_renderer('frontend/plugins/contests', '../../../templates/layout').scoreboard(course, start, end, blackout, tasks, results, activity)
    # except:
    #        raise web.notfound()


class ContestAdmin(object):

    """ Contest settings for a course """

    def GET(self, courseid):
        """ GET request: simply display the form """
        course = get_course_and_check_rights(courseid)
        contest_data = get_contest_data(course)
        return get_template_renderer('frontend/plugins/contests', '../../../templates/layout').admin(course, contest_data, None, False)

    def POST(self, courseid):
        """ POST request: update the settings """
        course = get_course_and_check_rights(courseid)
        contest_data = get_contest_data(course)

        new_data = web.input()
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
            save_contest_data(course, contest_data)
            return get_template_renderer('frontend/plugins/contests', '../../../templates/layout').admin(course, contest_data, None, True)
        else:
            return get_template_renderer('frontend/plugins/contests', '../../../templates/layout').admin(course, contest_data, errors, False)


def init(plugin_manager, config):
    """
        Init the contest plugin.
        Available configuration:
        ::

            {
                "plugin_module": "frontend.plugins.contests.contests"
            }
    """

    plugin_manager.add_page('/contest/([^/]+)', ContestScoreboard)
    plugin_manager.add_page('/admin/([^/]+)/contest', ContestAdmin)
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    plugin_manager.add_hook('modify_task_data', modify_task_data)
    plugin_manager.add_hook('header_html', additional_headers)
    plugin_manager.add_hook('course_menu', course_menu)
