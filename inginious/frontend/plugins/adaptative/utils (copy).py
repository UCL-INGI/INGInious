


# Maybe put in common/task_factory
def get_testing_tasks(course, courseid):
	test_tasks = []
	task_names = course._task_factory.get_readable_tasks(course)
	for name in task_names:
		new_name = name.replace("/", "")
		test_tasks.append(new_name)
	return test_tasks


def update_level_task(db, taskid, level):
	db.levels.update({"taskid": taskid},{"$setOnInsert": {"taskid": taskid, "level": level}}, upsert=True)
	
	
def get_level_task(db, taskid):
	return db.levels.find_one({"taskid": taskid})['level']


def get_test_state(db, username):
	state = db.test_state.find_one({"user": username})
	if state != None:
		return (state["user"], state["q_index"], state["testing_limit"], state["already_asked"], state["succeeded"], state["current_level"], state["finished"], state["task"], state["course"], state["current_task"])
	return None	
	
	
def update_test_state(db, username, q_index, testing_limit, already_asked, results, level, finished, taskid, courseid, current_task):
	db.test_state.update({"user": username},{"$set": {"user": username, "q_index": q_index, "testing_limit": testing_limit, "already_asked": already_asked,  "succeeded" : results, "current_level" : level, "finished" : finished, "task" : taskid, "course" : courseid, "current_task" : current_task}}, upsert=True)


