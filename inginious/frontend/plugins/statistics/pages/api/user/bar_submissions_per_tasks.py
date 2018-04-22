import web

from .user_api import UserApi

class BarSubmissionsPerTasksApi(UserApi):
    def statistics(self):
        username = self.user_manager.session_username()
        course_id = web.input().course_id

        submissions_per_task = self.database.submissions.aggregate([
            {
                "$match":
                    {
                        "username": [username],
                        "courseid": course_id,
                        "custom.summary_result": {"$ne": None}
                    }
            },
            {
                "$group": {
                    "_id":
                        {
                            "summary_result": "$custom.summary_result",
                            "task_id": "$taskid"
                        },
                    "count": {"$sum": 1}
                }
            },
            {
                "$project":
                    {
                        "_id": 0,
                        "task_id": "$_id.task_id",
                        "summary_result": "$_id.summary_result",
                        "count": 1
                    }
            },
            {
                "$sort": {"task_id": -1}
            }
        ])

        course = self.course_factory.get_course(course_id)
        course_tasks = course.get_tasks()
        sorted_tasks = sorted(course_tasks.values(), key=lambda task: task.get_order())

        task_id_to_statistics = {}
        for element in submissions_per_task:
            task_id = element["task_id"]

            if task_id not in task_id_to_statistics:
                task_id_to_statistics[task_id] = []

            task_id_to_statistics[task_id].append({
                "count": element["count"],
                "summary_result": element["summary_result"]
            })

        submissions_per_task = []

        for task in sorted_tasks:
            _id = task.get_id()
            verdicts = task_id_to_statistics.get(_id, [])
            for verdict in verdicts:
                submissions_per_task.append({
                    "task_id": _id,
                    "summary_result": verdict["summary_result"],
                    "count": verdict["count"]
                })

        return 200, submissions_per_task
