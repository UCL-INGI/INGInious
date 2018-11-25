import random
from rpy2.robjects import r
from random import randrange, sample
from inginious.frontend.plugins.adaptative.utils import get_level_task
import scipy.stats
r('library(catR)')


"""
	Functions useful for Computerized Adaptative Testing 
"""


def get_parameters(tasks, db):
	"""
		Returns a list of lists, containing each the paramaters for each tasks 
	"""
	parameters = []
	
	for task in tasks:
		diff = get_level_task(db, task)#task_level_evaluation(task, db)
		parameters.append([1, diff, 0, 1])
		
	return parameters


def task_level_evaluation(task, database):
	"""
		Gives an estimate of the probability to succeed a task based on people that already submitted
	"""
	submissions = database.submissions.find({'taskid' : task})
	(nb_users_success, nb_users_total) = get_nb_users(submissions)
	
	if(nb_users_total==0): return 0

	return nb_users_success/nb_users_total


def get_nb_users(submissions):
	""" 
		Returns a tuple s.t. (nbr users that succeed in the submissions, nbr users that submitted)
	"""
	users_success = []
	users_total = []
	Z
	for sub in submissions:
		if(sub['username'][0] not in users_total):
			users_total.append(sub['username'][0]) 
			
		if(sub['username'][0] not in users_success and sub['result']=='success'):
			users_success.append(sub['username'][0]) 
			
	return (len(users_success), len(users_total))
	

def ability_estimation(results):
	"""
		Returns a double representing the ability estimate given the results using thetaEst
	"""
	r("results <- NULL")
	
	for q in results: # building the list in R
		r("results <- c(results,c(%s))" % q)
		
	theta = r('theta <- thetaEst(itembank, x=results)')[0]
	standard_error = r("standard_error <- semTheta(theta, itembank)")[0]
	
	return (theta, standard_error)


def get_next_question(itembank, proficiency, already_answered, method):
	"""
		Returns the index of the next question
	"""
	r("already_answered <- NULL")
	
	for q in already_answered: # building the list in R
			r("already_answered <- c(already_answered,c(%s))" % q)
			
	indice = r('nextItem(itembank, theta=%s, criterion = "%s", out = already_answered)'% (proficiency, method))[0][0]
	
	return indice #itembank.rownames[indice-1]


def get_first_question(itembank, proficiency, method):
	"""
		Returns the index of the first question, choosen with the method 
	

		"MFI" (default): one selects the most informative item(s) for the given initial ability value(s);

		"bOpt": one selects the item(s) whose difficulty level is as close as possible to the inital ability value(s);

		"thOpt": one selects the item(s) with the ability value where they get their maximum Fisher information is as close as possible to the inital ability value(s) (see Magis, 2013, for further details);

		"progressive" for the progressive method (see nextItem);

		"proportional" for the proportional method (see nextItem).
		
		(found at https://www.rdocumentation.org/packages/catR/versions/3.13/topics/startItems)

	"""
	indice = r('startItems(itembank, startSelect = "%s", theta=%s)'% (method, proficiency))[0][0]
	return indice #itembank.rownames[indice-1]
	

def init_item_bank(question_set, database):
	"""	
	 Return an array in the form:
		       [,1] [,2] [,3] [,4]
	 cycle32       1  0.0    0    1
	 all_cycles    1  0.3    0    1
	 cycle22       1 -0.3    0    1
	 cycle23       1 -0.3    0    1
	 cycle41       1  0.3    0    1
	 cycle42       1  0.3    0    1
	 cycle21       1 -0.3    0    1
	 cycle43       1  0.3    0    1
	 cycle31       1  0.0    0    1
	 cycle33       1  0.0    0    1

	 given question_set: a set of names of questions
	 	   database: link to the database to get the for parameters of each tasks
	"""
	r("itembank <- NULL")
	r("questions <- NULL")
	r("items <- NULL")
	
	for q in question_set:
		r("questions <- c(questions,c('%s'))" % q)
		# Get the item bank
		parameters_matrix = get_parameters(question_set, database)
		
		for item in parameters_matrix:
			w = item[0]
			x = item[1]
			y = item[2]
			z = item[3]
			items = r('items <- c(items, c(%s,%s,%s,%s))' % (w,x,y,z))
			
	return r('itembank <- matrix(%s, ncol=4, nrow=%s, byrow=TRUE, dimnames=list(%s, NULL))' % ("items", len(question_set), "questions"))


