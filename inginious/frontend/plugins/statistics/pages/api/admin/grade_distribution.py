import collections
import web

from .admin_api import AdminApi

class GradeDistributionApi(AdminApi):
    def _compute_grade_distribution_statistics(self, course_id):
        all_grades = self.database.user_tasks.find(
            {"courseid": course_id},
            {"taskid": 1, "grade": 1, "username": 1}
        )

        grouped_grades = collections.defaultdict(list)
        for item in all_grades:
            task_id = item["taskid"]

            grouped_grades[task_id].append(item["grade"])

        return grouped_grades


    def API_GET(self):
        parameters = web.input()

        course_id = self.get_mandatory_parameter(parameters, 'course_id')
        course = self.get_course_and_check_rights(course_id)

        grade_distribution_statistics = self._compute_grade_distribution_statistics(course_id)
        statistics_by_grade_distribution = self.convert_task_dict_to_sorted_list(course, grade_distribution_statistics,
                                                                                 'grades', include_all_tasks=True)

        return 200, statistics_by_grade_distribution
