import collections
import web

from .admin_api import AdminApi
from .utils import task_submissions_detail

class SubmissionsByVerdictDetailsApi(AdminApi):

    def _compute_details(self, course_id, task_id, summary_result):
        submissions = self.database.submissions.aggregate([
            {"$match":
                {
                    "courseid": course_id,
                    "custom.summary_result": summary_result,
                    "taskid" : task_id
                }
            },
            {"$unwind":
                {
                    "path": "$username",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$sort": collections.OrderedDict([
                    ("submitted_on", -1),
                    ("username", 1)
                ])
            }
        ])

        return task_submissions_detail(submissions)

    def API_GET(self):
        parameters = web.input()
        course_id = self.get_mandatory_parameter(parameters, 'course_id')
        self.get_course_and_check_rights(course_id)

        task_id = self.get_mandatory_parameter(parameters, 'task_id')
        summary_result = self.get_mandatory_parameter(parameters, 'summary_result')

        submissions = self._compute_details(course_id, task_id, summary_result)

        return 200, submissions
