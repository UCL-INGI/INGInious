import logging
import json

_BASE_RENDERER_PATH = 'frontend/webapp/plugins/hooks_example'
_logger = logging.getLogger("inginious.frontend.webapp.plugins.hooks_example")

def init(plugin_manager, course_factory, client, config):

    def on_task_updated(courseid, taskid, new_content):
        task_name = new_content["name"]
        descriptor = course_factory.get_course(courseid)._task_factory.get_task_descriptor_content(courseid, taskid)
        task_author = descriptor["author"]
        task_context = descriptor["context"]
        tags = new_content.get("tags", [])
        task_data = {
            "task_name": task_name,
            "task_id": taskid,
            "task_author": task_author,
            "task_context": task_context,
            "course_id": courseid,
            "tags": tags
        }

        data_filter = {
            "task_id": taskid,
            "course_id": courseid
        }

        plugin_manager.get_database().tasks_cache.update_one(filter=data_filter,
                                                             update={"$set": task_data}, upsert=True)

    def on_task_deleted(courseid, taskid):
        data_filter = {
            "task_id": taskid,
            "course_id": courseid
        }
        plugin_manager.get_database().tasks_cache.delete_many(data_filter)

    def on_course_deleted(courseid):
        data_filter = {
            "course_id": courseid
        }
        plugin_manager.get_database().tasks_cache.delete_many(data_filter)

    def on_course_updated(courseid, new_content):
        course_data = {
            "course_id": new_content["name"]
        }
        data_filter = {
            "course_id": courseid
        }
        plugin_manager.get_database().tasks_cache.update_many(filter=data_filter,
                                                              update={"$set": course_data})

    if "tasks_cache" not in plugin_manager.get_database().collection_names():
        plugin_manager.get_database().create_collection("tasks_cache")
    plugin_manager.get_database().tasks_cache.create_index([("course_id", 1), ("task_id", 1)], unique=True)

    plugin_manager.add_hook('task_updated', on_task_updated)
    plugin_manager.add_hook('task_deleted', on_task_deleted)
    plugin_manager.add_hook('course_updated', on_course_updated)
    plugin_manager.add_hook('course_deleted', on_course_deleted)

