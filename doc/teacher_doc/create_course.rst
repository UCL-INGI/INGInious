Creating a new course
=====================

The directory structure for the courses and tasks in INGInious is:

::

	tasks/
		course_name_1.course
		course_name_1/
			task_1.task
			task_1/
				run
				...
			task_2.task
			task2/
				run
				...
		course_name_2.course
		course_name_2/
			task_1.task
			task_1/
				run
				...
			another.task
			another/
				run
				...

Most of the time (this is the case in INGI_) the teaching team do not have direct
access to the *tasks* folder, but only to the folder of the course it maintains.
If this is the case for you, you can skip this section and go directly to 
`Creating a new task`.

In the main *tasks* folder, each course (for example for the course with id *course_name*)
must have a *course_name.course* file, and a folder named *course_name*.

The *.course* are JSON files, containing basic informations about the course:
::

	{
		"admins": ["your ldap login"], 
		"name": "The complete name of the course"
	}

The syntax is self-explanatory.
Only username that are in the *admins* list are available to see students' submissions
and statistics. The *admins* is only needed when using the frontend.

.. _INGI: http://www.uclouvain.be/ingi.html