import web
import inginious.frontend.pages.api._api_page as api

from inginious.frontend.pages.api._api_page import APIAuthenticatedPage
from inginious.common.course_factory import CourseNotFoundException, CourseUnreadableException, InvalidNameException

class UserApi(APIAuthenticatedPage):
    def API_GET(self):
        self.validate_parameters()
        return self.statistics()

    def validate_parameters(self):
        username = self.user_manager.session_username()
        course_id = web.input(course_id=None).course_id

        if course_id is None:
            raise api.APIError(400, {"error": "course_id is mandatory"})

        try:
            course = self.course_factory.get_course(course_id)
        except (CourseNotFoundException, InvalidNameException, CourseUnreadableException):
            raise api.APIError(400, {"error": "The course does not exist or the user does not have permissions"})

        if not self.user_manager.course_is_user_registered(course, username):
            raise api.APIError(400, {"error": "The course does not exist or the user does not have permissions"})

    def statistics(self):
        return "[]"
