import inginious.frontend.pages.api._api_page as api
from inginious.common.course_factory import CourseNotFoundException, CourseUnreadableException, InvalidNameException


class AdminApi(api.APIAuthenticatedPage):
    def get_course_and_check_rights(self, course_id):
        try:
            course = self.course_factory.get_course(course_id)
        except (CourseNotFoundException, InvalidNameException, CourseUnreadableException):
            raise api.APIError(400, {"error": "The course does not exist or the user does not have permissions."})

        if not self.user_manager.has_admin_rights_on_course(course):
            raise api.APIError(400, {"error": "The course does not exist or the user does not have permissions."})

        return course
