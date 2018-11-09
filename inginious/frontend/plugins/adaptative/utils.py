

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
	Return the level of the task
"""
def get_level_task(db, taskid):
	return db.levels.find_one({"taskid": taskid})['level']


"""
	Return the test state
"""
def get_test_state(db, username):
	state = db.test_state.find_one({"user": username})
	if state != None:
		return (state["user"], state["level"], state["testing_limit"], state["current_question"], state["path"], state["answers"], )
	return None	
	
	
"""
	Update the test state which have the same username
"""
def update_test_state(db, username, level, testing_limit, current_question, path, answers):
	db.test_state.update({"user": username},{"$set": {"user": username, "level": level, "testing_limit": testing_limit, "current_question": current_question,  "path" : path, "answers" : answers}}, upsert=True)


