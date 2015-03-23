Tutorial
========

In this document we will describe how to create a simple task, that checks that a code in python returns "Hello World!".

Creating the task description
-----------------------------

The task description is a small YAML file describing everything that INGInious needs to know to verify the input of the student.

Here is a simple task description. Put this file with the name *task.yaml* in a newly created *helloworld* folder in your course directory.

::

    author: "Guillaume Derval"
    name: "Hello World!"
    context: "In this task, you will have to write a python script that displays 'Hello World!'."
    problems:
        question1:
            name: "Let's print it"
            header: "def func():"
            type: "code"
            language: "python"
    limits:
        time: 10
        memory: 50
        output: 1000
    environment: "default"

Most of the fields are self-explanatory. Some remarks:

- "problems" is a dictionnary of problem. Each problem must have an unique id, for example here "question1".
- the problem "question1" have its "type" field that equals to "code", which means the student must enter some code to answer the question. Other types exists, such as multiple-choice.
- "limits" are the limits that the task cannot exceed. The "time" is in second, and "memory" and "output" are in kilobytes.
- if you do not have any special need (other languages than python or c/c++), you do not need to change the "environment" field. It is intended to change the environment where the tasks run. Please see :doc:`create_container`.

Creating the run file
---------------------

In your task folder, you will put every file needed to test the input of the student.

Let's first create a template, where we will put the code of the student.

::

	def func():
	@	@question1@@

	func()

Name the file *template.py* for example. The syntax is very simple: put a first *@* on the line where you want to put the code of the student. Then indent the line and write a second *@*.
Now write the problem id of the problem you want to take the input from (*question1*) then write another *@*, write a possible suffix (not used here), and then finish the line with a last *@*.

Now we can create the file called *run*. *run* will be the script that is launched when the task is started. Here we will create a *bash* script, that parses the template and verifies its content.

::

	#! /bin/bash

	# This line parses the template and put the result in studentcode.py
	parsetemplate --output studentcode.py template.py

	# Verify the output of the code...
	output=$(python studentcode.py)
	if [ "$output" = "Hello World!" ]; then
		# The student succeeded
		feedback --result success --feedback "You solved this difficult task!"
	else
		# The student failed
		feedback --result failed --feedback "Your output is $output"
	fi

Here we use two commands provided by INGInious, parsetemplate and feedback. The code is commented and should be self-explanatory :-)

Put this content at the path helloworld/run and don't forget to give it the execution rights:

::

	$ chmod +x helloworld/run

Test it
-------

Your code should now work properly, you can restart the INGInious frontend and test it :-)

More documentation is available here: :doc:`create_task`.
