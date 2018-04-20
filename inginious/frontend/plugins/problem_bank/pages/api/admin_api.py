import inginious.frontend.pages.api._api_page as api
from inginious.common.course_factory import CourseNotFoundException, CourseUnreadableException, InvalidNameException

class AdminApi(api.APIAuthenticatedPage):
    def get_course_and_check_rights(self, course_id):
        try:
            course = self.course_factory.get_course(course_id)
        except (CourseNotFoundException, InvalidNameException, CourseUnreadableException):
            raise api.APIError(400, {"error": "Invalid course"})

        if not self.user_manager.has_staff_rights_on_course(course):
            raise api.APIError(400, {"error": "Invalid course"})

        return course

    def get_mandatory_parameter(self, parameters, parameter_name):
        if parameter_name not in parameters:
            raise api.APIError(400, {"error": parameter_name + " is mandatory"})

        return parameters[parameter_name]