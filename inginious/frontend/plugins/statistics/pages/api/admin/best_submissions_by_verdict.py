import web
from .admin_api import AdminApi

class BestSubmissionsByVerdictApi(AdminApi):

    def get_best_statistics_by_verdict(self, course):
        course_id = course.get_id()
        best_statistics_by_verdict = self.database.user_tasks.aggregate([
            {
                "$match":
                    {
                        "courseid": course_id
                    }
            },
            {
                "$lookup":
                    {
                        "from": "submissions",
                        "localField": "submissionid",
                        "foreignField": "_id",
                        "as": "submission"
                    }
            },
            {
                "$unwind":
                    {
                        "path": "$submission"
                    }
            },
            {
                "$group": {
                    "_id": {"summary_result": "$submission.custom.summary_result",
                            "taskid": "$taskid"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "task_id": "$_id.taskid",
                    "summary_result": "$_id.summary_result",
                    "count": 1
                }
            },
            {
                "$match":
                    {
                        "summary_result": {"$ne": None}
                    }
            }
        ])

        return best_statistics_by_verdict

    def API_GET(self):
        parameters = web.input()

        course_id = self.get_mandatory_parameter(parameters, "course_id")
        course = self.get_course_and_check_rights(course_id)

        best_statistics_by_verdict = self.get_best_statistics_by_verdict(course)
        course_tasks = course.get_tasks()
        sorted_tasks = sorted(course_tasks.values(), key=lambda task: task.get_order())

        task_id_to_statistics = {}
        for element in best_statistics_by_verdict:
            task_id = element["task_id"]

            if task_id not in task_id_to_statistics:
                task_id_to_statistics[task_id] = []

            task_id_to_statistics[task_id].append({
                "count": element["count"],
                "summary_result": element["summary_result"]
            })

        best_statistics_by_verdict = []

        for task in sorted_tasks:
            _id = task.get_id()
            verdicts = task_id_to_statistics.get(_id, [])
            for verdict in verdicts:
                best_statistics_by_verdict.append({
                    "task_id": _id,
                    "summary_result": verdict["summary_result"],
                    "count": verdict["count"]
                })
        return 200, best_statistics_by_verdict
