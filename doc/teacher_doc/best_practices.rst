Best practices
==============

Do not delete tasks
-------------------

Instead of deleting a task, it is better to make it unavailable, using the *accessible* field.

For example, if 2014-05-11 is the date where the task became unavailable:

::

	{
		...
		
		"accessible": "/2014-05-11",
		
		...
	
	}

Do not put the student's code directly in your tests
----------------------------------------------------

Inserting student's code direclty in your tests is dangerous, 
because the student could make syntax errors that would display the code of your tests.

It is better to put all the student's functions in a single template file, which one you will import in you test files.

Make small tests
----------------

Inside your tasks, do not test everything is a single test file.
Using a file for each test is a good practice, and will allow you to debug your code efficiently, 
while providing students fine-grained error descriptions.

Try to use unit-test libraries provided by your programming language.
