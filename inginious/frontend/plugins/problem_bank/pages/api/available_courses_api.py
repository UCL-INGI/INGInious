from .admin_api import AdminApi


class AvailableCoursesApi(AdminApi):
    def API_GET(self):
        all_courses = self.course_factory.get_all_courses()
        bank_course_ids = set(bank["courseid"] for bank in self.database.problem_banks.find())

        available_courses = [{
            'id': course_id,
            'name': course.get_name("en")
        } for course_id, course in all_courses.items() if course_id not in bank_course_ids]

        return 200, available_courses
