# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from inginious.frontend.pages.utils import INGIniousPage
from collections import OrderedDict
from inginious.frontend.plugins.adaptative.utils import  get_testing_tasks, update_level_task, get_test_state, update_test_state
from inginious.frontend.plugins.adaptative.cat import task_level_evaluation, student_level_evaluation, get_parameters, get_first_question, get_next_question, init_item_bank
from inginious.frontend.plugins.adaptative.hooks import adaptive_get_hook, adaptive_post_hook
from inginious.frontend.pages.tasks import BaseTaskPage

class HomePage(BaseTaskPage):
	def GET(self, courseid, config):
		username = self.user_manager.session_username()
		try:
			course = self.course_factory.get_course(courseid)
		except exceptions.CourseNotFoundException as ex:
			raise web.notfound(str(ex))
		print(course)
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
def home_plugin_parameters(config):
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
    """  course name, initial level"""
    #global course_name
    plugin_manager.add_hook("adaptive_get_hook", adaptive_get_hook)
    plugin_manager.add_hook("adaptive_post_hook", adaptive_post_hook)
    """ Init the plugin """
    plugin_manager.add_page("/adaptative/([^/]*)", home_plugin_parameters(plugin_config))
    plugin_manager.add_page("/adaptative/([^/]*)/([^.]*)", AdaptativePage)
