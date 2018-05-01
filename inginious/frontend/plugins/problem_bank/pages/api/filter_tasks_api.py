import web

from inginious.frontend.plugins.utils.admin_api import AdminApi
from inginious.frontend.plugins.utils import get_mandatory_parameter


class FilterTasksApi(AdminApi):
    def API_POST(self):

        parameters = web.input()
        task_query = get_mandatory_parameter(parameters, "task_query")
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

                task = self.database.tasks_cache.find_one({"_id": id_task["_id"]})

                dict_task = {"course_id": task["course_id"], "task_id": task["task_id"], "task_name": task["task_name"],
                        "task_author": task["task_author"], "task_context": task["task_context"],
                        "tags": self.list_names_tags(task["tags"])}
                tasks.append(dict_task)

        return 200, sorted(tasks, key=lambda k: (k['course_id'], k['task_id']))
