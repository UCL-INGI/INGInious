import web
import uuid
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from pymongo.errors import DuplicateKeyError


import inginious.frontend.pages.api._api_page as api
import os
from .api.admin_api import AdminApi
from inginious.common.exceptions import TaskNotFoundException
from inginious.common.course_factory import CourseNotFoundException, CourseUnreadableException, InvalidNameException
from inginious.common.filesystems.provider import NotFoundException
from inginious.frontend.plugins.problem_bank.constants import _REACT_BUILD_FOLDER, _REACT_BASE_URL

_BASE_RENDERER_PATH = 'frontend/plugins/problem_bank'

class CopyTaskApi(AdminApi):

    def is_a_bank(self, course_id):
        return self.database.problem_banks.find({"courseid": {"$eq": course_id}}).count() != 0

    def API_POST(self):
        parameters = web.input()
        target_id = self.get_mandatory_parameter(parameters, "target_id")
        bank_id = self.get_mandatory_parameter(parameters, "bank_id")
        task_id = self.get_mandatory_parameter(parameters, "task_id")

        target_course = self.get_course_and_check_rights(target_id)
        target_course_tasks_ids = [key for key in target_course.get_tasks()]

        copy_id = str(uuid.uuid4())
        while copy_id in target_course_tasks_ids:
            copy_id = str(uuid.uuid4())

        try:
            bank_course = self.course_factory.get_course(bank_id)
        except (CourseNotFoundException, InvalidNameException, CourseUnreadableException):
            raise api.APIError(400, {"error": "Invalid bank"})

        if not self.is_a_bank(bank_id):
            raise api.APIError(400, {"error": "Invalid bank"})

        try:
            task = bank_course.get_task(task_id)
        except (TaskNotFoundException, InvalidNameException):
            raise api.APIError(400, {"error": "Invalid task"})

        target_fs = self.course_factory.get_course_fs(target_id)

        try:
            target_fs.copy_to(task.get_fs().prefix, copy_id)

            if "tasks_cache" in self.database.collection_names():
                task_to_copy = self.database.tasks_cache.find_one({ "course_id": bank_id, "task_id": task_id })

                self.database.tasks_cache.insert({ "course_id": target_id, "task_id": copy_id,
                                                   "task_name": task_to_copy["task_name"],
                                                   "tags": task_to_copy["tags"],
                                                   "task_context": task_to_copy["task_context"],
                                                   "task_author": task_to_copy["task_author"]
                                                   })

        except NotFoundException:
            raise api.APIError(400, {"error": "the copy_id made an invalid path"})

        return 200, {"message": "Copied succesfully"}


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


class AvailableCoursesApi(AdminApi):
    def API_GET(self):
        all_courses = self.course_factory.get_all_courses()
        bank_course_ids = set(bank["courseid"] for bank in self.database.problem_banks.find())

        available_courses = [{
            'id': course_id,
            'name': course.get_name("en")
        } for course_id, course in all_courses.items() if course_id not in bank_course_ids]

        return 200, available_courses


class SearchTaskApi(AdminApi):
    def API_GET(self):
        bank_course_ids = set(bank["courseid"]
                              for bank in self.database.problem_banks.find())

        tasks = []
        for bank_course_id in bank_course_ids:
            search_tasks = self.database.tasks_cache.aggregate([
                {"$match":
                     {
                         "course_id": bank_course_id
                     }
                }
            ])
            for task in search_tasks:
                dict = {"course_id": task["course_id"], "task_id": task["task_id"], "task_name": task["task_name"],
                        "task_author": task["task_author"], "task_context": task["task_context"],
                        "tags": self.parse_tags(task["tags"])}
                tasks.append(dict)

        return 200, sorted(tasks, key=lambda k: (k['course_id'], k['task_id']))

    def parse_tags(self, tags):
        parsed_tags = list()
        for key, tag in tags.items():
            parsed_tags.append(tag["name"])
        return parsed_tags


class FilterTasksApi(AdminApi):
    def API_POST(self):

        parameters = web.input()
        task_query = self.get_mandatory_parameter(parameters, "task_query")
        bank_course_ids = set(bank["courseid"]
                              for bank in self.database.problem_banks.find())

        tasks = []
        for bank_course_id in bank_course_ids:
            ids_tasks = self.database.tasks_cache.aggregate([
                    {"$match":
                        {
                            "course_id": bank_course_id
                        }
                    },
                    {"$unwind":
                        {
                            "path": "$tags",
                            "preserveNullAndEmptyArrays": True
                        }
                    },
                    {"$match":
                        {"$or":
                            [{"course_id": {"$regex": ".*" + task_query + ".*"}},
                             {"task_name": {"$regex": ".*" + task_query + ".*"}},
                             {"tags": {"$regex": ".*" + task_query + ".*"}}]
                        }
                    },
                    {"$group":
                         {"_id": "$_id"}
                    }
            ])

            for id_task in ids_tasks:

                task = self.database.tasks_cache.find_one({ "_id": id_task["_id"] })

                dict = {"course_id": task["course_id"], "task_id": task["task_id"], "task_name": task["task_name"],
                        "task_author": task["task_author"], "task_context": task["task_context"],
                        "tags": self.parse_tags(task["tags"])}
                tasks.append(dict)

        return 200, sorted(tasks, key=lambda k: (k['course_id'], k['task_id']))

    def parse_tags(self, tags):
        parsed_tags = list()
        for key, tag in tags.items():
            parsed_tags.append(tag["name"])
        return parsed_tags

class BankPage(INGIniousAdminPage):
    def _list_files_recursive(self, folder):
        return [os.path.relpath(os.path.join(root, name), folder) for root, _, files in os.walk(folder) for name in files]

    def _set_up_compiled_resources(self, build_folder, base_url):
        if not base_url.endswith('/'):
            base_url += '/'

        css_base_folder = 'static/css'
        css_local_folder = os.path.join(build_folder, css_base_folder)
        css_files = [name for name in self._list_files_recursive(css_local_folder) if name.endswith('.css')]

        for file in css_files:
            self.template_helper.add_css(base_url + 'static/css/' + file)

        js_base_folder = 'static/js'
        js_local_folder = os.path.join(build_folder, js_base_folder)
        js_files = [name for name in self._list_files_recursive(js_local_folder) if name.endswith('.js')]

        for file in js_files:
            self.template_helper.add_javascript(base_url + 'static/js/' + file)

    def GET_AUTH(self):
        self._set_up_compiled_resources(_REACT_BUILD_FOLDER, _REACT_BASE_URL)

        return (
            self.template_helper.get_custom_renderer(_BASE_RENDERER_PATH).index()
        )