import web

from pymongo.errors import DuplicateKeyError
from .admin_api import AdminApi


class ManageBanksCoursesApi(AdminApi):
    def get_course_id(self):
        parameters = web.input()
        course_id = self.get_mandatory_parameter(parameters, "course_id")
        self.get_course_and_check_rights(course_id)
        return course_id

    def API_GET(self):
        return 200, [bank["courseid"] for bank in self.database.problem_banks.find()]

    def API_POST(self):
        course_id = self.get_course_id()
        try:
            self.database.problem_banks.insert({"courseid": course_id})
        except DuplicateKeyError:
            return 200, {"message": "Course already a bank"}

        return 200, {"message": "Bank created successfully"}

    def API_DELETE(self):
        course_id = self.get_course_id()

        rows_affected = self.database.problem_banks.remove({"courseid": {"$eq": course_id}}, True)["n"]

        if rows_affected >= 1:
            return 200, {"message": "Bank removed successfully"}
        else:
            return 404, {"message": "No bank found"}
