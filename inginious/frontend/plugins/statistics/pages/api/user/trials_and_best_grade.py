import web

from .user_api import UserApi

class TrialsAndBestGradeApi(UserApi):
    def statistics(self):
        username = self.user_manager.session_username()
        course_id = web.input().course_id

        best_submissions = self.database.user_tasks.aggregate([
            {
                "$match":
                    {
                        "username": username,
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
                "$sort":
                    {
                        "submission.submitted_on": 1
                    }

            },
            {
                "$project":
                    {
                        "_id": 0,
                        "result": "$submission.custom.summary_result",
                        "taskid": 1,
                        "tried": 1,
                        "grade": 1
                    }
            },
            {
                "$match":
                    {
                        "result": {"$ne": None}
                    }
            }
        ])

        return 200, list(best_submissions)
