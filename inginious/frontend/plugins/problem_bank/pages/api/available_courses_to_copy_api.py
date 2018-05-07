from inginious.frontend.plugins.utils.admin_api import AdminApi


class AvailableCoursesToCopyApi(AdminApi):
    def API_GET(self):
        all_courses = self.course_factory.get_all_courses()

        available_courses = [{
            'id': course_id,
            'name': course.get_name(self.user_manager.session_language())
        } for course_id, course in all_courses.items() if self.user_manager.has_admin_rights_on_course(course)]

        return 200, available_courses
