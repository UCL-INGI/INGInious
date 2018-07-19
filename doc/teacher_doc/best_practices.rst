Best practices
==============

Use YAML with RST
-----------------

YAML with RST is the recommended way to create task descriptions. Old methods such as JSON+RST, 
JSON+HTML and RST+RST are deprecated and were dropped. If you really want to use them, these parsing methods are still available as plugins.

Provide a test set for the student to test their code themselves, and grade the code with at least this set
-----------------------------------------------------------------------------------------------------------

This will allow the students to make sure that they submit properly. If a test set that is public works
on the student's computer but does not work on INGInious, this is the sign of a greater problem.
Give them a complete feedback on these public tests, but hide the rest to keep the difficulty of the task.

Do not use the "file" subproblem type
-------------------------------------

When you ask student to produce some code, 
you should *always* put a "code" subproblem, where the student can copy-paste his code.
INGInious is made to receive text as input, no (huge) binary files. 

Using Jar, Zip, Tar+Gz and other formats to convey code in binary format is most of the time convenient for the task writer, 
but it's not the case for the students; tools for compressing files are not always consistent among all OS, 
and even inside the same OS, leading to errors that could be easily avoided using text input.

It is also prone to other types of errors: when submitting a project with a zip file or a jar, task writers ask most of the time
to resubmit the complete project, with other files that may seem uneeded by the grader and that was maybe modified by the student.
There is then two possibilities: 

* either the task writer effectively uses these files, leading to an error that is not really due to the student
* or the task writer does not use them, and there is a waste of disk space

These "common files" should be located not in the code submitted by the student, but directly in the task folder.

Using "code" inputs forces you to only ask the students to submit what is really needed, improving the quality of the tasks.
Zip, Jar and other archive formats should only be used when grading huge projects.

If you still have to use a "file" subproblem type, make it lightweight
----------------------------------------------------------------------

For example, when submitting a Jar file (type of archive for languages that uses the JVM), 
please do not ask student to add common libraries (such as Scala) in their submission. 
These libraries can be installed in the task folder, or even better, directly in the container.

INGInious reloads most of the time the whole submission when it needs to read something inside, 
and reloading a file of 20M can take time.

Students should only have to upload files they modified, *and not files common to all submissions*.

If you still have to use a lightweight "file" subproblem, ask for code, not for binary executables
--------------------------------------------------------------------------------------------------

Asking for binary executable (or JVM bytecode, etc.) is a bad practice from a general point of view:
* You cannot read the code of the students to check the grading
* Small differences in libs used on the system and in the container can lead to errors. Even in the JVM.
* It will force the grader to recompile the code of the student, allowing to make more checks

You should always ask *only* the code (no binary executable, no JVM .class file, ...) and *always* recompile everything.

Do not delete tasks
-------------------

Instead of deleting a task, it is better to make it unavailable, using the *accessible* field.

For example, if 2014-05-11 is the date where the task became unavailable::

	{
		...
		"accessible": "/2014-05-11",
		...
	}

Do not put the student's code directly in your tests
----------------------------------------------------

Inserting student's code directly in your tests is dangerous,
because the student could make syntax errors that would display the code of your tests.

It is better to put all the student's functions in a single template file, which one you will import in you test files.

Use student container
---------------------

To be completely secure, run anything you do not trust inside a separate *student container*.
Students may want to interfere with the normal work of your grading script to get better grades...

Make small tests
----------------

Inside your tasks, do not test everything in a single test file.
Using a file for each test is a good practice, and will allow you to debug your code efficiently,
while providing students fine-grained error descriptions.

Try to use unit-test libraries provided by your programming language.
