# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.
import sys
import web
from inginious.frontend.pages.utils import INGIniousPage
from collections import OrderedDict
from inginious.frontend.plugins.adaptative.utils import  get_testing_tasks, update_level_task, get_test_state, update_test_state
from inginious.frontend.plugins.adaptative.cat import task_level_evaluation, ability_estimation, get_parameters, get_first_question, get_next_question, init_item_bank
from inginious.frontend.plugins.adaptative.hooks import adaptive_get_hook, adaptive_post_hook, task_buttons_hook, course_button_hook
from inginious.frontend.pages.tasks import BaseTaskPage


def plugin_parameters(config):
	"""
		Return a tuple containing the parameters of the plugin
	"""
	
	stopping_criterion = config["stopping_criterion"]
		
	if "length" in stopping_criterion:
		nbr_questions = config["questions_limit"]
	else:
		nbr_questions = sys.maxint
	
	first_item_method = config["first_item_selection"]
	next_item_selection = config["next_item_selection"]
	ability = config["initial_level"]
	
	return first_item_method, next_item_selection, stopping_criterion, nbr_questions, ability 


class HomePage(BaseTaskPage):
		
	def GET(self, courseid, config):
		username = self.user_manager.session_username()
		
		try:
			course = self.course_factory.get_course(courseid)
		except exceptions.CourseNotFoundException as ex:
			raise web.notfound(str(ex))
		
		test_state = get_test_state(self.database, username)	
		items_names = get_testing_tasks(course, courseid)
		items_bank = init_item_bank(items_names, self.database)
		
		if(test_state != None):
			(username, ability, testing_limit, current_question_index, path, answers, method) = test_state	
			is_finished = len(path) == int(testing_limit)
			
			if is_finished: 
				(ability, standard_error) = ability_estimation(answers)
				return self.template_helper.get_custom_renderer('frontend/plugins/adaptative').test_end(answers, ability.__round__(3))
			else: # load the last quesiton in path
				taskid = items_bank.rownames[int(path[len(path)-1])-1]
		
		else: # newcomers
			(first_item_method, next_item_selection, stopping_criterion, nbr_questions, ability) = plugin_parameters(config)
			answers = ['NA'] * len(items_names) 
			next_task_index = get_first_question(items_bank, ability, first_item_method)
			path = [next_task_index]
			taskid = items_bank.rownames[next_task_index-1]
			update_test_state(self.database, username, ability, nbr_questions, next_task_index, path, answers, next_item_selection)
		
		try:
			task = course.get_task(taskid)
		except exceptions.TaskNotFoundException as ex:
			raise web.notfound(str(ex))
			
		return self.template_helper.get_custom_renderer('frontend/plugins/adaptative').home_test(course, task)

		
def home_plugin_parameters(config):
	"""
		Return an instance of the class displaying the page with plugin parameters as arguments in the GET method
	"""
	class HomeAdaptativePage(INGIniousPage):
				def GET(self, course):
					return HomePage(self).GET(course, config)
	return HomeAdaptativePage 


class AdaptativePage(INGIniousPage):
	def GET(self, testCourse, testTask):
	    return BaseTaskPage(self).GET(testCourse, testTask, False)

	def POST(self, testCourse, testTask):
	    return BaseTaskPage(self).POST(testCourse, testTask, False)
		

def init(plugin_manager, course_factory, client, plugin_config):
    plugin_manager.add_hook("adaptive_get_hook", adaptive_get_hook)
    plugin_manager.add_hook("adaptive_post_hook", adaptive_post_hook)
    plugin_manager.add_hook("task_buttons_hook", task_buttons_hook)
    plugin_manager.add_hook("course_button_hook", course_button_hook)
    
    """ Init the plugin """
    plugin_manager.add_page("/adaptative/([^/]*)", home_plugin_parameters(plugin_config))
    plugin_manager.add_page("/adaptative/([^/]*)/([^.]*)", AdaptativePage)
