import collections
import web

from .admin_api import AdminApi

class GradeCountApi(AdminApi):
    def _compute_grade_count_statistics(self, course_id):
        statistics_by_grade = self.database.user_tasks.aggregate([
            {"$match": {"courseid": course_id}},
            {
                "$group": {
                    "_id": {"grade": {"$ceil": "$grade"}, "task": "$taskid"},
                    "count": {"$sum": 1}
                }
            }
        ])

        task_id_to_statistics = collections.defaultdict(list)
        for element in statistics_by_grade:
            task_id = element["_id"]["task"]

            task_id_to_statistics[task_id].append({
                "grade": element["_id"]["grade"],
                "count": element["count"]
            })

        return task_id_to_statistics

    def API_GET(self):
        parameters = web.input()

        course_id = self.get_mandatory_parameter(parameters, 'course_id')
        course = self.get_course_and_check_rights(course_id)

        grade_count_statistics = self._compute_grade_count_statistics(course_id)
        statistics_by_grade_count = self.convert_task_dict_to_sorted_list(course, grade_count_statistics, 'grades',
                                                                          include_all_tasks=True)

        return 200, statistics_by_grade_count
