from inginious.frontend.plugins.adaptative.utils import  get_testing_tasks, update_level_task, get_test_state, update_test_state
from inginious.frontend.plugins.adaptative.cat import task_level_evaluation, student_level_evaluation, get_parameters, get_first_question, get_next_question, init_item_bank

"""
	- Render the page: test_end or taskview
	- Choose next task
	- Update test state 
	
	at each GET request

"""
def adaptive_get_hook(username, page, course, courseid, task, taskid, students, eval_submission, user_task, random_input_list):
	test_state = get_test_state(page.database, username)
	if(test_state != None):
		items_names = get_testing_tasks(course, courseid)
		items_bank = init_item_bank(items_names, page.database)
		(username, level, testing_limit, current_question_index, path, answers) = test_state
		task_index = items_bank.rownames.index(taskid) + 1 # index in bank
		if(task_index not in path): # multiple gets
			is_finished = len(path) == int(testing_limit)
			if is_finished: 
				student_level = student_level_evaluation(answers)
				return page.template_helper.get_custom_renderer('frontend/plugins/adaptative', layout=True).test_end(answers, student_level.__round__(3))

			else:
				path.append(task_index)
				next_task_index = get_next_question(items_bank, level, path)
				next_task_name = items_bank.rownames[int(next_task_index)-1]
				next_task_object = course.get_task(next_task_name)
				update_test_state(page.database, username, level, testing_limit, next_task_index, path, answers)
				return page.template_helper.get_custom_renderer('frontend/plugins/adaptative',layout=True).task_view(course, task, page.submission_manager.get_user_submissions(task), students, eval_submission, user_task, page.webterm_link, next_task_object, random_input_list)
		else:
			next_task_index = get_next_question(items_bank, level, path)
			next_task_name = items_bank.rownames[int(next_task_index)-1]
			next_task_object = course.get_task(next_task_name)
			return page.template_helper.get_custom_renderer('frontend/plugins/adaptative', layout=True).task_view(course, task, page.submission_manager.get_user_submissions(task), students, eval_submission, user_task, page.webterm_link, next_task_object, random_input_list)


"""
	- Update the answers given by the student
	- Update the level of the student
	
	at each POST request

"""
def adaptive_post_hook(username, page, result):
	test_state = get_test_state(page.database, username)
	(username, level, testing_limit, current_question_index, path, answers) = test_state
	if(result['result']=="failed" and answers[path[len(path)-1]-1] == 'NA'): 
		answers[path[len(path)-1]-1] = '0'
	elif result['result']=="success":  
		answers[path[len(path)-1]-1] = '1'
	level = student_level_evaluation(answers)
	update_test_state(page.database, username, level, testing_limit, current_question_index, path, answers)


