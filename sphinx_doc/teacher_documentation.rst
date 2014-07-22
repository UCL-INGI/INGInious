Teacher's documentation
=======================

What is INGInious?
------------------

Made by the INGI_ departement at the Catholic University of Louvain, 
INGInious is a tool built in Python_ on the top of Docker_, that allows teacher to 
automatize the test on the code made by the students.

INGInious is completely langage-agnostic: you can make containers_ for every langage that
you can run on a Linux distribution.

.. _Python: http://www.python.org/
.. _Docker: https://www.docker.com/
.. _INGI: http://www.uclouvain.be/ingi.html

How does INGInious work?
````````````````````````

INGInious is basicly a backend (which is, in Python, the :doc:`backend`) which receives 
the code of the student and send it to a Docker container_. The Docker container then mades
some verification on the code of the student and returns a status, that can be *success*,
*crash*, *timeout*, or *failed*.

INGInious also provides a frontend (you guessed it, this is the :doc:`frontend` in Python)
. Made with MongoDB as database, the frontend is in fact an extension of the backend,
and allows students to work directly on a website.
Statistics are available for the teachers through a dedicated interface.

Docker containers
'''''''''''''''''

.. _container:
.. _containers:

Docker containers are small virtual operating systems that provides isolation_ with the
processes and ressource of the host operating system.
Docker allow to create and ship any software on any free Linux distribution.

As there are no hypervisor, the processes launched in the container are in fact directly
run by the host operating system, which allows applications to be amazingly fast.

Docker allow teachers to build new containers easily, to add new dependencies to the test
made on the student's code.

Isolation
'''''''''
.. _isolation:

Isolation allows teachers and system administrators to stop worrying about the code that
the students provides. 

For example, if a student provides a forkbomb instead of a good code for the 
test, the forkbomb will be contained inside the container. The host operating system
(the computer that runs INGInious) won't be affected.

The same thing occurs with memory consumption and disk flood. The running time of a code
is also limited.

Compatibility
`````````````

INGInious provides two compatibly layers with the non-longer-maintained Pythia Project.
Tools to convert old Pythia tasks to INGInious tasks are available in the folder
`dev_tools`.

The converted tasks are then 100% compatible with INGInious.

Creating a new course
---------------------

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

Creating a new task
-------------------

Task description files
``````````````````````

Inside a course folder (see `Creating a new course`) tasks must have 
(for example with *taskname* as task id) a file *taskname.task* and a folder named
*taskname*.

The *.task* file is a JSON file containing informations about the task.
::
	{
		"author": "Your name",
		"context": "The context of this task. Explain here what the students have to do.",
		"order": 1,
		"name": "The complete name of this task",
		"problems":
		{
			"a_problem_id":
			{
				"header": "A header for this question",
				"type": "code",
				"language": "c"
			}
		},
		"limits":
		{
			"time": 30,
			"memory": 32,
			"output": 5210
		},
		"environment": "default"
	}

*author*, *context*, *order*, *name*, *language* and *header* are only needed 
if you use the frontend. 
*context* and *header* are parsed using restructuredText [#]_ .
*order* is an integer, used by the frontend to sort the task list. Task are sorted
in increasing value of *order*.

*problems* describes sub-problems of this task. This field is mandatory and must contain
at least one problem. Problem types are described in the following section 
`Problem types`_. Each problem must have an id which is alphanumeric and unique.

*environment* is the name of the Docker container in which the student's code will run.
This field is only needed if there is code to correct; a multiple-choice question does
not need it.

.. [#] There are some options about using HTML instead of restructuredText, but they
       are purposely not documented :-)
       
Problem types
'''''''''''''

Code problems
.............

*"type"="code"* problems allows students to submit their code. The code is then
sent to a container where a script made by the teaching team corrects it.

Here is a simple example for a code problem
::
	{
		"type": "code",
		"language": "c",
		"header": "Hello dear student!",
		"name": "A name"
	}

*header* and *language* are only needed when using the frontend and are not mandatory. 
This description typically displays on the frontend a box where student 
can put their code.

Code problem input's are available in the *run* script (see `Run file`_) directly with the
id of the problem.

Single code line problems
.........................

*"type":"code-single-line"* is simply a code box that allows a single line as input.
::
	{
		"type": "code-single-line",
		"language": "c",
		"header": "Hello dear student!",
		"name": "Another problem"
	}

Single line code problem input's are available in the *run* script (see `Run file`_) directly with the
id of the problem.

Advanced code problem
.....................

Advanced code problems are available:

::

	{
		"type": "code",
		"header": "some text",
		"name": "And again, another name",
		"boxes":
		{
			"boxId1":
			{
				"type": "text",
				"content": "Some additionnal text"
			},
			"boxId2":
			{
				"type": "input-text",
				"maxChars": 10
			},
			"boxId3":
			{
				"type": "multiline",
				"maxChars": 1000,
				"lines": 8,
				"language": "java"
			}
		}
	}
	
*Boxes* are displayable (on the frontend) input fields that allows the student
to fill more than one entry per problem. Different box types are available, all of them
are demonstrated above. Every configuration in the boxes (*maxChars*,*lines*,*language*)
is not mandatory, except *content* if the box type is *text*.

In the *run* file (see `Run file`_), boxes input are available with the name 
*problem_id.box_id*

Match problems
..............

Match problem are input that allows a single-line input from the student and that
returns if the student entered exactly the text given in the "answer" field.

::

	{
		"name": "The answer",
		"type": "match",
		"header": "some text describing this problem",
		"answer": "42"
	}

Match problem input's are available in the *run* script (see `Run file`_) 
directly with the id of the problem.

Multiple choice problems
........................

::

	{
		"name": "An exercice",
		"type": "multiple-choice",
		"header": "The answer to life, the universe and any other things is",
		"multiple": true,
		"limit": 2,
		"choices":
		[
			{
				"text":"It is, of course, 42!",
				"valid"=true
			},
			{
				"text":"It should be *42*",
				"valid"=true
			},
			{text:"43!"},
			{text:"41?"},
		]
	}
	
Choices are described in the *choices* section of the JSON. Each choice must have
a *text* field (on the frontend) that will be parsed in restructuredText. Valid choices
must have a *"valid"=true* field.

*multiple* indicates if the student may (or not) select more than one response.

Choices are chosen randomly in the list. If the *limit* field is set, the number of
choices taken equals to the limit. There is always a valid answer in the chosen choices.

Multiple choice problem input's are available in the *run* script (see `Run file`_) 
directly with the id of the problem. The input can be either an array of 
integer if *multiple* is true or an integer. Choices are numbered sequentially from 0.

Run file
````````

When the student have submit his/her code, INGInious starts a new Docker container
with the right *environment* for the task (as given in the *.task* file). Inside this
container is launched a script, called *run*, that you have to provide in the
directory of your task.

Here is a simple example of a *run* file, compatible with the *default* environment,
that simply returns that the student's code is OK:
::
	
	#! /bin/bash
	feedback --result success

The *run* script is simply an executable application (a bash script, a python script, or 
a compiled executable runnable by the container). INGInious' default containers provides
commands (also available as python libraries) to interact with the backend.

Usable commands in the *run* file
'''''''''''''''''''''''''''''''''

feedback
........

TODO