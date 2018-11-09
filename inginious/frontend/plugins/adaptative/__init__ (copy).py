# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.plugins.adaptative.test import AdaptativePage
from collections import OrderedDict
from inginious.frontend.plugins.adaptative.utils import  get_testing_tasks, update_level_task, get_test_state, update_test_state
from inginious.frontend.plugins.adaptative.cat import task_level_evaluation, student_level_evaluation, get_parameters, get_first_question, get_next_question, init_item_bank, get_label_from_index, get_labels_from_indices
from inginious.frontend.pages.tasks import BaseTaskPage

class HomePage(BaseTaskPage):
	def GET(self):
		username = self.user_manager.session_username()
		
		# Choose a number in function of available questions
		nbr_questions = 5
		courseid = "aga"
		
		try:
			course = self.course_factory.get_course(courseid)
		except exceptions.CourseNotFoundException as ex:
			raise web.notfound(str(ex))
			
		test_state = get_test_state(self.database, username)	
		
		# the test has already begun
		if(test_state != None):
			(username, question_index, testing_limit, already_asked, test_submission_result, level, finished, testTaskid, testCourseid, previous_task) = test_state	
			
			# the test is finished
			if int(question_index) > int(testing_limit): 
				student_level = student_level_evaluation(test_submission_result)
				print("\nLevel: " + str(student_level) + "\n")
				return self.template_helper.get_custom_renderer('frontend/plugins/adaptative').test_end(get_labels_from_indices(already_asked, test_submission_result), student_level.__round__(3))
			
			# the test is not finished
			else:  
			
				#student_level = student_level_evaluation(test_submission_result)
				#task_index = get_next_question(student_level, already_asked)
				#already_asked.append(task_index)
				#taskid = get_label_from_index(task_index)
				taskid = previous_task
				#print("\nLevel: " + str(student_level) + " / Choosen task: " + str(taskid) + "\n")
				#update_test_state(self.database, username, question_index + 1, testing_limit, already_asked, test_submission_result, student_level, False, None, courseid, taskid)
				
		# Create a new test for the current user		
		else:	
			test = get_testing_tasks(course, courseid)
			init_item_bank(test, self.database)
			test_submission_result = ['NA'] * len(test)
			(question_index, level, already_asked, testing_limit) = (0, student_level_evaluation(test_submission_result), [], nbr_questions)
			task_index = get_first_question(level)
			#already_asked.append(task_index)
			taskid = get_label_from_index(task_index)
			print("\nLevel: " + str(level) + " / Choosen task: " + str(taskid) + "\n")
			update_test_state(self.database, username, question_index + 1, testing_limit, already_asked, test_submission_result, level, False, taskid, courseid, taskid)
		
		try:
			task = course.get_task(taskid)
		except exceptions.TaskNotFoundException as ex:
			raise web.notfound(str(ex))
			
		return self.template_helper.get_custom_renderer('frontend/plugins/adaptative').home_test(course, task)

class HomeAdaptativePage(INGIniousPage):
	def GET(self):
		return HomePage(self).GET()
    
def init(plugin_manager, course_factory, client, plugin_config):
    """ Init the plugin """
    plugin_manager.add_page("/adaptative", HomeAdaptativePage)
    #plugin_manager.add_page("/adaptative/intrain", AdaptativePage)
    plugin_manager.add_page("/adaptative/([^/]*)/([^.]*)", AdaptativePage)
    #plugin_manager.add_page("/adaptative/intest/(.*)/(.*)", AdaptativePage)
