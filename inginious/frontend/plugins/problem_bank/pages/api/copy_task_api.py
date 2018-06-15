import web
import uuid

import inginious.frontend.pages.api._api_page as api
from inginious.frontend.plugins.utils.admin_api import AdminApi
from inginious.frontend.plugins.utils import get_mandatory_parameter
from inginious.common.exceptions import TaskNotFoundException
from inginious.common.course_factory import CourseNotFoundException, CourseUnreadableException, InvalidNameException
from inginious.common.filesystems.provider import NotFoundException


class CopyTaskApi(AdminApi):

    def is_a_bank(self, course_id):
        return self.database.problem_banks.find({"courseid": {"$eq": course_id}}).count() != 0

    def API_POST(self):
        parameters = web.input()
        target_id = get_mandatory_parameter(parameters, "target_id")
        bank_id = get_mandatory_parameter(parameters, "bank_id")
        task_id = get_mandatory_parameter(parameters, "task_id")
        target_course = self.get_course_and_check_rights(target_id)
        target_course_tasks_ids = [key for key in target_course.get_tasks()]

        copy_id = str(uuid.uuid4())
        while copy_id in target_course_tasks_ids:
            copy_id = str(uuid.uuid4())

        try:
            bank_course = self.course_factory.get_course(bank_id)
        except (CourseNotFoundException, InvalidNameException, CourseUnreadableException):
            raise api.APIError(400, {"error": "Invalid bank"})

        if not self.is_a_bank(bank_id) and not self.user_manager.has_admin_rights_on_course(bank_course):
            raise api.APIError(400, {"error": "Invalid bank"})

        try:
            task = bank_course.get_task(task_id)
        except (TaskNotFoundException, InvalidNameException):
            raise api.APIError(400, {"error": "Invalid task"})

        target_fs = self.course_factory.get_course_fs(target_id)

        try:
            target_fs.copy_to(task.get_fs().prefix, copy_id)

            if "tasks_cache" in self.database.collection_names():
                task_to_copy = self.database.tasks_cache.find_one({"course_id": bank_id, "task_id": task_id})

                self.database.tasks_cache.insert(
                    {
                        "course_id": target_id,
                        "task_id": copy_id,
                        "task_name": task_to_copy["task_name"],
                        "tags": task_to_copy["tags"],
                        "task_context": task_to_copy["task_context"],
                        "task_author": task_to_copy["task_author"],
                        "course_name": target_course.get_name(self.user_manager.session_language())
                    })

        except NotFoundException:
            raise api.APIError(400, {"error": "the copy_id made an invalid path"})

        return 200, {"message": "Copied successfully"}
