# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" A scoreboard, based on the usage of the "custom" dict in submissions.
    It uses the key "score" to retrieve score from submissions
"""
from collections import OrderedDict
import web

from inginious.frontend.webapp.pages.utils import INGIniousAuthPage


class ScoreBoardCourse(INGIniousAuthPage):
    """ Page displaying the different available scoreboards for the course """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course = self.course_factory.get_course(courseid)
        scoreboards = course.get_descriptor().get('scoreboard', [])

        try:
            names = {i: val["name"] for i, val in enumerate(scoreboards)}
        except:
            raise web.notfound("Invalid configuration")

        if len(names) == 0:
            raise web.notfound()

        return self.template_helper.get_custom_renderer('frontend/webapp/plugins/scoreboard').main(course, names)


def sort_func(overall_result_per_user, reverse):
    def sf(user):
        score = overall_result_per_user[user]["total"]
        solved = overall_result_per_user[user]["solved"]

        return (-solved, (-score if not reverse else score))
    return sf


class ScoreBoard(INGIniousAuthPage):
    """ Page displaying a specific scoreboard """

    def GET_AUTH(self, courseid, scoreboardid):  # pylint: disable=arguments-differ
        """ GET request """
        course = self.course_factory.get_course(courseid)
        scoreboards = course.get_descriptor().get('scoreboard', [])

        try:
            scoreboardid = int(scoreboardid)
            scoreboard_name = scoreboards[scoreboardid]["name"]
            scoreboard_content = scoreboards[scoreboardid]["content"]
            scoreboard_reverse = bool(scoreboards[scoreboardid].get('reverse', False))
        except:
            raise web.notfound()

        # Convert scoreboard_content
        if isinstance(scoreboard_content, str):
            scoreboard_content = OrderedDict((scoreboard_content, 1))
        if isinstance(scoreboard_content, list):
            scoreboard_content = OrderedDict([(entry, 1) for entry in scoreboard_content])
        if not isinstance(scoreboard_content, OrderedDict):
            scoreboard_content = OrderedDict(iter(scoreboard_content.items()))

        # Get task names
        task_names = {}
        for taskid in scoreboard_content:
            try:
                task_names[taskid] = course.get_task(taskid).get_name()
            except:
                raise web.notfound("Unknown task id "+taskid)

        # Get all submissions
        results = self.database.submissions.find({
            "courseid": courseid,
            "taskid": {"$in": list(scoreboard_content.keys())},
            "custom.score": {"$exists": True},
            "result": "success"
        }, ["taskid", "username", "custom.score"])

        # Get best results per users(/group)
        result_per_user = {}
        users = set()
        for submission in results:
            # Be sure we have a list
            if not isinstance(submission["username"], list):
                submission["username"] = [submission["username"]]
            submission["username"] = tuple(submission["username"])

            if submission["username"] not in result_per_user:
                result_per_user[submission["username"]] = {}


            if submission["taskid"] not in result_per_user[submission["username"]]:
                result_per_user[submission["username"]][submission["taskid"]] = submission["custom"]["score"]
            else:
                # keep best score
                current_score = result_per_user[submission["username"]][submission["taskid"]]
                new_score = submission["custom"]["score"]
                task_reversed = scoreboard_reverse != (scoreboard_content[submission["taskid"]] < 0)
                if task_reversed and current_score > new_score:
                    result_per_user[submission["username"]][submission["taskid"]] = new_score
                elif not task_reversed and current_score < new_score:
                    result_per_user[submission["username"]][submission["taskid"]] = new_score


            for user in submission["username"]:
                users.add(user)

        # Get user names
        users_realname = {}
        for username, userinfo in self.user_manager.get_users_info(users).items():
            users_realname[username] = userinfo[0] if userinfo else username

        # Compute overall result per user, and sort them
        overall_result_per_user = {}
        for key, val in result_per_user.items():
            total = 0
            solved = 0
            for taskid, coef in scoreboard_content.items():
                if taskid in val:
                    total += val[taskid]*coef
                    solved += 1
            overall_result_per_user[key] = {"total": total, "solved": solved}
        sorted_users = list(overall_result_per_user.keys())
        sorted_users = sorted(sorted_users, key=sort_func(overall_result_per_user, scoreboard_reverse))

        # Compute table
        table = []

        # Header
        if len(scoreboard_content) == 1:
            header = ["", "Student(s)", "Score"]
            emphasized_columns = [2]
        else:
            header = ["", "Student(s)", "Solved", "Total score"] + [task_names[taskid] for taskid in list(scoreboard_content.keys())]
            emphasized_columns = [2, 3]

        # Lines
        old_score = ()
        rank = 0
        for user in sorted_users:
            # Increment rank if needed, and display it
            line = []
            if old_score != (overall_result_per_user[user]["solved"], overall_result_per_user[user]["total"]):
                rank += 1
                old_score = (overall_result_per_user[user]["solved"], overall_result_per_user[user]["total"])
                line.append(rank)
            else:
                line.append("")

            # Users
            line.append(",".join(sorted([users_realname[u] for u in user])))

            if len(scoreboard_content) == 1:
                line.append(overall_result_per_user[user]["total"])
            else:
                line.append(overall_result_per_user[user]["solved"])
                line.append(overall_result_per_user[user]["total"])
                for taskid in scoreboard_content:
                    line.append(result_per_user[user].get(taskid, ""))

            table.append(line)

        renderer = self.template_helper.get_custom_renderer('frontend/webapp/plugins/scoreboard')
        return renderer.scoreboard(course, scoreboardid, scoreboard_name, header, table, emphasized_columns)


def course_menu(course, template_helper):
    """ Displays the link to the scoreboards on the course page, if the plugin is activated for this course """
    scoreboards = course.get_descriptor().get('scoreboard', [])

    if scoreboards != []:
        return str(template_helper.get_custom_renderer('frontend/webapp/plugins/scoreboard', layout=False).course_menu(course))
    else:
        return None


def task_menu(course, task, template_helper):
    """ Displays the link to the scoreboards on the task page, if the plugin is activated for this course and the task is used in scoreboards """
    scoreboards = course.get_descriptor().get('scoreboard', [])
    try:
        tolink = []
        for sid, scoreboard in enumerate(scoreboards):
            if task.get_id() in scoreboard["content"]:
                tolink.append((sid, scoreboard["name"]))

        if tolink:
            return str(template_helper.get_custom_renderer('frontend/webapp/plugins/scoreboard', layout=False).task_menu(course, tolink))
        return None
    except:
        return None


def init(plugin_manager, _, _2, _3):
    """
        Init the plugin.
        Available configuration in configuration.yaml:
        ::

            - plugin_module: "inginious.frontend.webapp.plugins.scoreboard"

        Available configuration in course.yaml:
        ::

            - scoreboard: #you can define multiple scoreboards
                - content: "taskid1" #creates a scoreboard for taskid1
                  name: "Scoreboard task 1"
                - content: ["taskid2", "taskid3"] #creates a scoreboard for taskid2 and taskid3 (sum of both score is taken as overall score)
                  name: "Scoreboard for task 2 and 3"
                - content: {"taskid4": 2, "taskid5": 3} #creates a scoreboard where overall score is 2*score of taskid4 + 3*score of taskid5
                  name: "Another scoreboard"
                  reverse: True #reverse the score (less is better)
    """
    page_pattern_course = r'/scoreboard/([a-z0-9A-Z\-_]+)'
    page_pattern_scoreboard = r'/scoreboard/([a-z0-9A-Z\-_]+)/([0-9]+)'
    plugin_manager.add_page(page_pattern_course, ScoreBoardCourse)
    plugin_manager.add_page(page_pattern_scoreboard, ScoreBoard)
    plugin_manager.add_hook('course_menu', course_menu)
    plugin_manager.add_hook('task_menu', task_menu)
