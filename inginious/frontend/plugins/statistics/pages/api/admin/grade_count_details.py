import collections
import web

from .admin_api import AdminApi
from .utils import project_detail_user_tasks

class GradeCountDetailsApi(AdminApi):
    def _compute_details(self, course_id, grade, task_id):
        user_tasks = self.database.user_tasks.aggregate([
            {"$match": {"$and": [{"courseid": course_id}, {"taskid": task_id}, {"grade": {"$lte": grade}},
                                 {"grade": {"$gt": grade - 1}}]}},
            {
                "$lookup": {
                    "from": "submissions",
                    "localField": "submissionid",
                    "foreignField": "_id",
                    "as": "submission"
                }
            },
            {
                "$unwind":
                    {
                        "path": "$submission",
                        "preserveNullAndEmptyArrays": True
                    }
            },
            {
                "$sort": collections.OrderedDict([
                    ("submission.submitted_on", -1),
                    ("username", 1)
                ])
            }
        ])

        return project_detail_user_tasks(user_tasks)

    def API_GET(self):
        parameters = web.input()

        course_id = self.get_mandatory_parameter(parameters, 'course_id')
        self.get_course_and_check_rights(course_id)

        grade = int(self.get_mandatory_parameter(parameters, 'grade'))
        task_id = self.get_mandatory_parameter(parameters, 'task_id')

        submissions = self._compute_details(course_id, grade, task_id)

        return 200, submissions
