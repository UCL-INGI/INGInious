import web

from pymongo.errors import DuplicateKeyError
from inginious.frontend.plugins.utils.admin_api import AdminApi
from inginious.frontend.plugins.utils import get_mandatory_parameter


class ManageBanksCoursesApi(AdminApi):
    def get_course_id(self):
        parameters = web.input()
        course_id = get_mandatory_parameter(parameters, "course_id")
        return course_id

    def API_GET(self):
        bank_courses = [{
            "id": bank["courseid"],
            "name": bank["course_name"],
            "is_removable": self.user_manager.has_admin_rights_on_course(self.course_factory.get_course(bank["courseid"]))
        } for bank in self.database.problem_banks.find()]

        return 200, bank_courses

    def API_POST(self):
        course_id = self.get_course_id()
        course = self.get_course_and_check_rights(course_id)

        if not course.is_open_to_non_staff():
            return 400, {"error": "Course cannot be added to bank. It is a hidden course."}

        try:
            self.database.problem_banks.insert({
                "courseid": course_id,
                "course_name": course.get_name(self.user_manager.session_language())
            })
        except DuplicateKeyError:
            return 200, {"message": "Course already a bank"}

        return 200, {"message": "Bank created successfully"}

    def API_DELETE(self):
        course_id = self.get_course_id()
        self.get_course_and_check_rights(course_id)

        rows_affected = self.database.problem_banks.remove({"courseid": {"$eq": course_id}}, True)["n"]

        if rows_affected >= 1:
            return 200, {"message": "Bank removed successfully"}
        else:
            return 404, {"error": "No bank found"}
