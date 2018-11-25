from inginious.common.filesystems.local import LocalFSProvider
from inginious.common.course_factory import create_factories
from inginious.frontend.tasks import WebAppTask
from inginious.frontend.courses import WebAppCourse
from inginious.frontend.task_problems import *

# Return a list of names of all task in the course
def get_testing_tasks(course, courseid):
	test_tasks = []
	task_names = course._task_factory.get_readable_tasks(course)
	for name in task_names:
		new_name = name.replace("/", "")
		test_tasks.append(new_name)
	return test_tasks


"""
	Update the task level
"""
def update_level_task(db, taskid, level):
	db.levels.update({"taskid": taskid},{"$setOnInsert": {"taskid": taskid, "level": level}}, upsert=True)
	
	
"""
	Return the level of the task if it exists in database; else it assigns 0.0 level to the new task;
"""
def get_level_task(db, taskid):
	try:
		level = db.levels.find_one({"taskid": taskid})['level']
	except TypeError: # we do not have an entry for this task
		print("Task " + taskid + " has been registered with level 0.0")
		level = 0.0 
		update_level_task(db, taskid, level)
	return level


"""
	Return the test state; None if it does not exist
"""
def get_test_state(db, username):
	state = db.test_state.find_one({"user": username})
	if state != None:
		return (state["user"], state["level"], state["testing_limit"], state["current_question"], state["path"], state["answers"], state["task_selection"] )
	return None	
	
	
"""
	Update the test state which have the same username
"""
def update_test_state(db, username, level, testing_limit, current_question, path, answers, task_selection):
	db.test_state.update({"user": username},{"$set": {"user": username, "level": level, "testing_limit": testing_limit, "current_question": current_question,  "path" : path, "answers" : answers, "task_selection": task_selection}}, upsert=True)


