from inginious.frontend.plugins.utils.admin_api import AdminApi


class AvailableTasksApi(AdminApi):

    def API_GET(self):
        course_ids = set(bank["courseid"]
                         for bank in self.database.problem_banks.find())

        all_courses = self.course_factory.get_all_courses()
        for course_id, course in all_courses.items():
            if self.user_manager.has_admin_rights_on_course(course):
                course_ids.add(course_id)

        tasks = []
        for course_id in course_ids:
            search_tasks = self.database.tasks_cache.aggregate([
                {
                    "$match":
                        {
                            "course_id": course_id
                        }
                }
            ])
            for task in search_tasks:
                dict_task = {"course_id": task["course_id"], "task_id": task["task_id"], "task_name": task["task_name"],
                             "task_author": task["task_author"], "task_context": task["task_context"],
                             "tags": task["tags"], "course_name": task["course_name"]
                             }
                tasks.append(dict_task)

        return 200, sorted(tasks, key=lambda k: (k['course_id'], k['task_id']))
