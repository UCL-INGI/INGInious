from inginious.frontend.plugins.utils.admin_api import AdminApi


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
                dict_task = {"course_id": task["course_id"], "task_id": task["task_id"], "task_name": task["task_name"],
                        "task_author": task["task_author"], "task_context": task["task_context"],
                        "tags": self.list_names_tags(task["tags"])}
                tasks.append(dict_task)

        return 200, sorted(tasks, key=lambda k: (k['course_id'], k['task_id']))

