# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for computation of statistics  """
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from datetime import datetime, date, timedelta


class CourseStatisticsPage(INGIniousAdminPage):
    def _tasks_stats(self, courseid, tasks, daterange):
        stats_tasks = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
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

    def _users_stats(self, courseid, daterange):
        stats_users = self.database.submissions.aggregate([
            {"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
            {"$project": {"username": "$username", "result": "$result"}},
            {"$unwind": "$username"},
            {"$group": {"_id": "$username", "submissions": {"$sum": 1}, "validSubmissions":
                {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
             },
            {"$sort": {"submissions": -1}}])

        return [
            {"name": x["_id"],
             "submissions": x["submissions"],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_users
        ]

    def _graph_stats(self, courseid, daterange):
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

        stats_graph = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": min_date, "$lt": max_date+delta1}, "courseid": courseid}},
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
        return (all_submissions, valid_submissions)

    def GET_AUTH(self, courseid, f=None, t=None):  # pylint: disable=arguments-differ
        """ GET request """
        course, __ = self.get_course_and_check_rights(courseid)
        tasks = course.get_tasks()
        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        error = None
        if f == None and t == None:
            daterange = [now - timedelta(days=14), now]
        else:
            try:
                daterange = [datetime.strptime(x[0:16], "%Y-%m-%dT%H:%M") for x in (f,t)]
            except:
                error = "Invalid dates"
                daterange = [now - timedelta(days=14), now]

        stats_tasks = self._tasks_stats(courseid, tasks, daterange)
        stats_users = self._users_stats(courseid, daterange)
        stats_graph = self._graph_stats(courseid, daterange)

        return self.template_helper.get_renderer().course_admin.stats(course, stats_graph, stats_tasks, stats_users, daterange, error)


def compute_statistics(course, data, ponderation):
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