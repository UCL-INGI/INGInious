# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for computation of statistics  """
from collections import OrderedDict

import flask

from inginious.frontend.pages.course_admin.utils import make_csv, INGIniousSubmissionsAdminPage
from datetime import datetime, date, timedelta


class CourseStatisticsPage(INGIniousSubmissionsAdminPage):
    def _tasks_stats(self, tasks, filter, limit):
        stats_tasks = self.database.submissions.aggregate(
            [{"$match": filter},
             {"$limit": limit},
             {"$project": {"taskid": "$taskid", "result": "$result"}},
             {"$group": {"_id": "$taskid", "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              },
             {"$sort": {"submissions": -1}}])

        return [
            {"name": tasks[x["_id"]].get_name(self.user_manager.session_language()) if x["_id"] in tasks else x["_id"],
             "submissions": x["submissions"],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_tasks
        ]

    def _users_stats(self, filter, limit):
        stats_users = self.database.submissions.aggregate([
            {"$match": filter},
            {"$limit": limit},
            {"$project": {"username": "$username", "result": "$result"}},
            {"$unwind": "$username"},
            {"$group": {"_id": "$username", "submissions": {"$sum": 1}, "validSubmissions":
                {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
             },
            {"$limit": limit},
            {"$sort": {"submissions": -1}}])

        return [
            {"name": x["_id"],
             "submissions": x["submissions"],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_users
        ]

    def _graph_stats(self, daterange, filter, limit):
        project = {
            "year": {"$year": "$submitted_on"},
            "month": {"$month": "$submitted_on"},
            "day": {"$dayOfMonth": "$submitted_on"},
            "result": "$result"
        }
        groupby = {"year": "$year", "month": "$month", "day": "$day"}

        method = "day"
        if (daterange[1] - daterange[0]).days < 7:
            project["hour"] = {"$hour": "$submitted_on"}
            groupby["hour"] = "$hour"
            method = "hour"

        min_date = daterange[0].replace(minute=0, second=0, microsecond=0)
        max_date = daterange[1].replace(minute=0, second=0, microsecond=0)
        delta1 = timedelta(hours=1)
        if method == "day":
            min_date = min_date.replace(hour=0)
            max_date = max_date.replace(hour=0)
            delta1 = timedelta(days=1)

        filter["submitted_on"] = {"$gte": min_date, "$lt": max_date+delta1}

        stats_graph = self.database.submissions.aggregate(
            [{"$match": filter},
             {"$limit": limit},
             {"$project": project},
             {"$group": {"_id": groupby, "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              },
             {"$sort": {"_id": 1}}])

        increment = timedelta(days=(1 if method == "day" else 0), hours=(0 if method == "day" else 1))

        all_submissions = {}
        valid_submissions = {}

        cur = min_date
        while cur <= max_date:
            all_submissions[cur] = 0
            valid_submissions[cur] = 0
            cur += increment

        for entry in stats_graph:
            c = datetime(entry["_id"]["year"], entry["_id"]["month"], entry["_id"]["day"], 0 if method == "day" else entry["_id"]["hour"])
            all_submissions[c] += entry["submissions"]
            valid_submissions[c] += entry["validSubmissions"]

        all_submissions = sorted(all_submissions.items())
        valid_submissions = sorted(valid_submissions.items())
        return all_submissions, valid_submissions

    def submission_url_generator(self, taskid):
        """ Generates a submission url """
        return "?tasks=" + taskid

    def _progress_stats(self, course):
        data = list(self.database.user_tasks.aggregate(
            [
                {
                    "$match":
                        {
                            "courseid": course.get_id(),
                            "username": {"$in": self.user_manager.get_course_registered_users(course, False)}
                        }
                },
                {
                    "$group":
                        {
                            "_id": "$taskid",
                            "viewed": {"$sum": 1},
                            "attempted": {"$sum": {"$cond": [{"$ne": ["$tried", 0]}, 1, 0]}},
                            "attempts": {"$sum": "$tried"},
                            "succeeded": {"$sum": {"$cond": ["$succeeded", 1, 0]}}
                        }
                }
            ]))
        tasks = course.get_task_dispenser().get_ordered_tasks()

        # Now load additional information
        result = OrderedDict()
        for taskid in tasks:
            result[taskid] = {"name": tasks[taskid].get_name(self.user_manager.session_language()), "viewed": 0,
                              "attempted": 0, "attempts": 0, "succeeded": 0, "url": self.submission_url_generator(taskid)}
        for entry in data:
            if entry["_id"] in result:
                result[entry["_id"]]["viewed"] = entry["viewed"]
                result[entry["_id"]]["attempted"] = entry["attempted"]
                result[entry["_id"]]["attempts"] = entry["attempts"]
                result[entry["_id"]]["succeeded"] = entry["succeeded"]
        return result

    def _global_stats(self, course, tasks, filter, limit, best_submissions_list, pond_stat):
        submissions = self.database.submissions.find(filter)
        if limit is not None:
            submissions.limit(limit)

        data = list(submissions)
        for d in data:
            d["best"] = d["_id"] in best_submissions_list  # mark best submissions

        return compute_statistics(course, tasks, data, pond_stat)

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        user_input = flask.request.args.copy()
        user_input["users"] = flask.request.args.getlist("users")
        user_input["audiences"] = flask.request.args.getlist("audiences")
        user_input["tasks"] = flask.request.args.getlist("tasks")
        user_input["org_categories"] = flask.request.args.getlist("org_categories")
        params = self.get_input_params(user_input, course, 500)

        return self.page(course, params)

    def POST_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)

        user_input = flask.request.form.copy()
        user_input["users"] = flask.request.form.getlist("users")
        user_input["audiences"] = flask.request.form.getlist("audiences")
        user_input["tasks"] = flask.request.form.getlist("tasks")
        user_input["org_categories"] = flask.request.form.getlist("org_categories")
        params = self.get_input_params(user_input, course, 500)

        return self.page(course, params)

    def page(self, course, params):
        msgs = []
        daterange = [None, None]
        try:
            if params.get('date_before', ''):
                daterange[1] = datetime.strptime(params["date_before"], "%Y-%m-%d %H:%M:%S")
            if params.get('date_after', ''):
                daterange[0] = datetime.strptime(params["date_after"], "%Y-%m-%d %H:%M:%S")
        except ValueError:  # If match of datetime.strptime() fails
            msgs.append(_("Invalid dates"))

        if daterange[0] is None or daterange[1] is None:
            now = datetime.now().replace(minute=0, second=0, microsecond=0)
            daterange = [now - timedelta(days=14), now]

        params["date_before"] = daterange[1].strftime("%Y-%m-%d %H:%M:%S")
        params["date_after"] = daterange[0].strftime("%Y-%m-%d %H:%M:%S")
        display_hours = (daterange[1] - daterange[0]).days < 4

        users, tutored_users, audiences, tutored_audiences, tasks, limit = self.get_course_params(course, params)

        filter, best_submissions_list = self.get_submissions_filter(course, only_tasks=params["tasks"],
                                             only_tasks_with_categories=params["org_categories"],
                                             only_users=params["users"],
                                             only_audiences=params["audiences"],
                                             grade_between=[
                                                 float(params["grade_min"]) if params.get('grade_min', '') else None,
                                                 float(params["grade_max"]) if params.get('grade_max', '') else None
                                             ],
                                             submit_time_between=[x.strftime("%Y-%m-%d %H:%M:%S") for x in daterange],
                                             keep_only_crashes="crashes_only" in params)

        stats_tasks = self._tasks_stats(tasks, filter, limit)
        stats_users = self._users_stats(filter, limit)
        stats_graph = self._graph_stats(daterange, filter, limit)
        stats_progress = self._progress_stats(course)
        stats_global = self._global_stats(course, tasks, filter, limit, best_submissions_list, params.get('stat', 'normal') == 'pond_stat')

        if "progress_csv" in flask.request.args:
            return make_csv(stats_progress)

        return self.template_helper.render("course_admin/stats.html", course=course, users=users,
                                           tutored_users=tutored_users, audiences=audiences,
                                           tutored_audiences=tutored_audiences, tasks=tasks, old_params=params,
                                           stats_graph=stats_graph, stats_tasks=stats_tasks, stats_users=stats_users,
                                           stats_progress=stats_progress, stats_global=stats_global,
                                           display_hour=display_hours, msgs=msgs)


def compute_statistics(course, tasks, data, ponderation):
    """ 
    Compute statistics about submissions and tags.
    This function returns a tuple of lists following the format describe below:
    (   
        [('Number of submissions', 13), ('Evaluation submissions', 2), …], 
        [(<tag>, '61%', '50%'), (<tag>, '76%', '100%'), …]
    )
     """
    
    super_dict = {}
    for submission in data:
        task = tasks.get(submission["taskid"], None)
        if task:
            username = "".join(submission["username"])
            tags_of_course = [tag for key, tag in course.get_tags().items() if tag.get_type() in [0,1]]
            for tag in tags_of_course:
                super_dict.setdefault(tag, {})
                super_dict[tag].setdefault(username, {})
                super_dict[tag][username].setdefault(submission["taskid"], [0,0,0,0])
                super_dict[tag][username][submission["taskid"]][0] += 1
                if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                    super_dict[tag][username][submission["taskid"]][1] += 1

                if submission["best"]:
                    super_dict[tag][username][submission["taskid"]][2] += 1
                    if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                        super_dict[tag][username][submission["taskid"]][3] += 1

    output = []
    for tag in super_dict:

        if not ponderation: 
            results = [0,0,0,0]
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    for i in range (0,4):
                        results[i] += super_dict[tag][username][task][i] 
            output.append((tag, 100*safe_div(results[1],results[0]), 100*safe_div(results[3],results[2])))


        #Ponderation by stud and tasks
        else:
            results = ([], [])
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    a = super_dict[tag][username][task]
                    results[0].append(safe_div(a[1],a[0]))
                    results[1].append(safe_div(a[3],a[2]))
            output.append((tag, 100*safe_div(sum(results[0]),len(results[0])), 100*safe_div(sum(results[1]),len(results[1]))))

    return (fast_stats(data), output)

def fast_stats(data):
    """ Compute base statistics about submissions """
    
    total_submission = len(data)
    total_submission_best = 0
    total_submission_best_succeeded = 0
        
    for submission in data:
        if "best" in submission and submission["best"]:
            total_submission_best = total_submission_best + 1
            if "result" in submission and submission["result"] == "success":
                total_submission_best_succeeded += 1
        
    statistics = [
        (_("Number of submissions"), total_submission),
        (_("Evaluation submissions (Total)"), total_submission_best),
        (_("Evaluation submissions (Succeeded)"), total_submission_best_succeeded),
        (_("Evaluation submissions (Failed)"), total_submission_best - total_submission_best_succeeded),
        # add here new common statistics
        ]
    
    return statistics
    
def safe_div(x,y):
    """ Safe division to avoid /0 errors """
    if y == 0:
        return 0
    return x / y