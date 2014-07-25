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

There are other fields that are available in the frontend:

-   *accessible*:
    ::
    
        "accessible": "2014-05-21 / 2014-05-28 00:00:00"
    	
    When this field is defined, the course is only available if it match the *available* check.
    This field can contain theses values:
	
    *true*
        the task is always accessible
    *false*
        the task is never accessible
    *"START"*
        where *START* is a valid date, like "2014-05-10 10:11:12", or "2014-06-18".
        The task is only accessible after *START*.
    *"/END"*
        where *END* is a valid date, like "2014-05-10 10:11:12", or "2014-06-18".
        The task is only accessible before *END*.
    *"START/END"*
        where *START* and *END* are valid dates, like "2014-05-10 10:11:12", or 
        "2014-06-18". The task is only accessible between *START* and *END*.

-   *nofrontend*:
	if this field is defined and is *true*, then the course won't be displayed on the frontend, but will still be available for the plugins.

.. _INGI: http://www.uclouvain.be/ingi.html