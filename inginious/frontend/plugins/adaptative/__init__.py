# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.plugins.adaptative.test import AdaptativePage
from collections import OrderedDict
from inginious.frontend.plugins.adaptative.utils import  get_testing_tasks, update_level_task, get_test_state, update_test_state
from inginious.frontend.plugins.adaptative.cat import task_level_evaluation, student_level_evaluation, get_parameters, get_first_question, get_next_question, init_item_bank
from inginious.frontend.pages.tasks import BaseTaskPage

class HomePage(BaseTaskPage):
	def GET(self, config):
		username = self.user_manager.session_username()
		courseid = config["course_name"]
		try:
			course = self.course_factory.get_course(courseid)
		except exceptions.CourseNotFoundException as ex:
			raise web.notfound(str(ex))
			
		test_state = get_test_state(self.database, username)	
		items_names = get_testing_tasks(course, courseid)
		items_bank = init_item_bank(items_names, self.database)
		if(test_state != None):
			(username, level, testing_limit, current_question_index, path, answers) = test_state	
			is_finished = len(path) == int(testing_limit)
			if is_finished: 
				student_level = student_level_evaluation(answers)
				return self.template_helper.get_custom_renderer('frontend/plugins/adaptative').test_end(answers, student_level.__round__(3))
			else: # load the last quesiton in path
				taskid = items_bank.rownames[int(path[len(path)-1])-1]
			
		else: # newcomers
			nbr_questions = config["nbr_questions"]
			answers = ['NA'] * len(items_names) 
			level = config["initial_level"] # starting level
			next_task_index = get_first_question(items_bank, level)
			path = [next_task_index]
			taskid = items_bank.rownames[next_task_index-1]
			update_test_state(self.database, username, level, nbr_questions, next_task_index, path, answers)
		try:
			task = course.get_task(taskid)
		except exceptions.TaskNotFoundException as ex:
			raise web.notfound(str(ex))
			
		return self.template_helper.get_custom_renderer('frontend/plugins/adaptative').home_test(course, task)


"""
	Return an instance of the class displaying the page with plugin parameters as arguments in the GET method
"""
def plugin_parameters(config):
	class HomeAdaptativePage(INGIniousPage):
				def GET(self):
					return HomePage(self).GET(config)
	return HomeAdaptativePage 
		
		
"""
	- Render the page: test_end or taskview
	- Choose next task
	- Update test state 
	
	at each GET request

"""
def get_hook(username, page, course, courseid, task, taskid, students, eval_submission, user_task, random_input_list):
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
def post_hook(username, page, result):
	test_state = get_test_state(page.database, username)
	(username, level, testing_limit, current_question_index, path, answers) = test_state
	if(result['result']=="failed" and answers[path[len(path)-1]-1] == 'NA'): 
		answers[path[len(path)-1]-1] = '0'
	elif result['result']=="success":  
		answers[path[len(path)-1]-1] = '1'
	level = student_level_evaluation(answers)
	update_test_state(page.database, username, level, testing_limit, current_question_index, path, answers)


def init(plugin_manager, course_factory, client, plugin_config):
    """  course name, initial level"""
    #global course_name
    plugin_manager.add_hook("get_hook", get_hook)
    plugin_manager.add_hook("post_hook", post_hook)
    """ Init the plugin """
    plugin_manager.add_page("/adaptative", plugin_parameters(plugin_config))
    plugin_manager.add_page("/adaptative/([^/]*)/([^.]*)", AdaptativePage)
