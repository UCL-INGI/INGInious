Run file
========

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

By default, the script is run inside the container in the /task directory, by a non-root
user. You can modify the container to change this (and everything else).

Usable commands in the *run* file
---------------------------------

feedback
````````

The *feedback* command allows you to set the result of your tests.
Every option is optionnal.

-r, --result STATUS		set the result to STATUS. STATUS can be
						success (the student succeeded the task),
						failed (there are error in the student answer),
						timeout (the tests timed out) or 
						crash (the tests crashed)
-f, --feedback MSG		set the feedback message to MSG. It is possible to set different
						messages for each problems. You can use *-i* to change the problem
						to which you assign the message
-i, --id PROBLEMID		set the problem id to which the message from the *-f* option is 
						assigned. Unused if *-f* is not set.

The *feedback* command can be called multiple times.

::

	feedback --result success --feedback "You're right, the answer is 42!"
	
getinput
````````

The *getinput* command returns the input given by the student for a specific problem id.
For example, for the problem id "pid", the command to do is:
::

	getinput pid
	
parsetemplate
`````````````

The *parsetemplate* command injects the input given by the student in a template.
The command has this form:
::
	
	parsetemplate [-o|--output outputfile] template
	
where *template* is the file to parse. Output file is the destination file.
If the *-o* option is not given, the template will be replaced.

The markup in the templates is very simple: *@prefix@problemid@suffix@*.
Prefix allows to correct the indentation when needed (this is useful in Python).

Example of template file (in java)
::
	
	public class Main
	{
		public static void main(String[] args)
		{
	@		@problem_one@@
		}
	}

archive
```````

*archive* allows you to put some data in an archive that will be returned to the frontend
and stored in the database for future reading. You can put there debug data, for example.

The command takes some arguments, which are all optionnal:

-o, --outsubdir	DIRECTORY		will put the file (specified with -a or -r)in the 
								specified sub-directory in the output archive
-a, --add FILEPATH				add the file to the archive
-r, --remove FILEPATH           remove the file from the archive
