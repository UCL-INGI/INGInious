Task description files
======================

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
				"name": "The title of this question",
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
-------------

Code problems
`````````````

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

Code problem input's are available in the *run* script (see :doc:`run_file`) directly with the
id of the problem.

Single code line problems
`````````````````````````

*"type":"code-single-line"* is simply a code box that allows a single line as input.
::

	{
		"type": "code-single-line",
		"language": "c",
		"header": "Hello dear student!",
		"name": "Another problem"
	}

Single line code problem input's are available in the *run* script (see :doc:`run_file`) directly with the
id of the problem.

Advanced code problem
`````````````````````

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

In the *run* file (see :doc:`run_file`), boxes input are available with the name 
*problem_id.box_id*

Match problems
``````````````

Match problem are input that allows a single-line input from the student and that
returns if the student entered exactly the text given in the "answer" field.

::

	{
		"name": "The answer",
		"type": "match",
		"header": "some text describing this problem",
		"answer": "42"
	}

Match problem input's are available in the *run* script (see :doc:`run_file`) 
directly with the id of the problem.

Multiple choice problems
````````````````````````

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

Multiple choice problem input's are available in the *run* script (see :doc:`run_file`) 
directly with the id of the problem. The input can be either an array of 
integer if *multiple* is true or an integer. Choices are numbered sequentially from 0.