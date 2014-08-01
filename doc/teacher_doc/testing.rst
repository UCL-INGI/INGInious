Testing a task
==============

Directly in the container
-------------------------

You can build a container by yourself and test your scripts directly inside the container.
To do so, you have to:

- Download and install Docker_ (on OS X, prefer docker-osx_ over Boot2Docker. docker-osx
  allows to mount local directory which is needed by INGInious)
- Download the source of the containers you use.
- Build all the containers you need by using the command
  ::
  	
  	sudo docker build -t inginious/containerfolder containerfolder
  
  Take care of the dependencies between the containers.
- Now that your container are built, you can now start one:
  ::
  
  	sudo docker run -v ~/taskDirectory:/ro/task -t -i inginious/youcontainer /bin/bash
  	
  Where *~/taskDirectory* is the folder containing your task data.
- You can then play inside the container. You have all powers inside the container.
  Remember that after you quit the container, any data you modified will be lost.

.. _Docker: https://www.docker.com/
.. _docker-osx: https://github.com/noplay/docker-osx

Unit-tests on tasks
-------------------

You can test your tasks thanks to several tools included in the default INGInious environment. 
Almost everything can be tested :

- Standard output given by the execution of your task
- Main result returned for a given set of inputs (success, or failed)
- Feedbacks given to the students
- User-defined pairs of tag and value

Tests can be described with input and output files, as described below.

Defining a new unit test
````````````````````````
If you want to check the correctness of your own assertions, you can use the tool 
*definetest* in your task code. This command must be called with the following syntax :
::

    definetest key value

where *key* is a tag, or an identifier, which will refer to the *value* you want to test at a
given execution point. The *value* argument is of type string.


Creating a new test batch
`````````````````````````
Now you've defined some tags for which you want to assert the value correctness, you can define some test files. 
These must be written in JSON with the following syntax. It must be like this :
::

    {
            "input": 
            {
                    "pid_1":"Answer to the problem with problem id pid_1",
                    "pid_2":"Answer to the problem with problem id pid_2"
            },
	    "result":"success",
            "tests": 
            {
                    "answer":"42"
            }
    }

In this example, *pid_1* and *pid_2* are two given problem id, which you defined in your task file. 
The value associated with theses keys are the input you would insert in the form field.

In this file, only the final result and the value of test tag *answer* are wanted to be checked with the specified expected values. More fields can be checked :

- *result* : the result of the execution of your task
- *text* : the general feedback given to the student
- *stdout* : the standard output produced by the execution of your task
- *problems* : a JSON entry containing pairs of problem identifiers and expected feedback
- *tests* : a JSON entry containing pairs of test tags and expected values

Not specified fields won't be checked during the testing process. So if you don't want to test the correctness of your standard output or feedback, just
omit these fields in the expected output file.

Testing a task with several test batches
````````````````````````````````````````

To test your task, you need to put your tests files together in the task directory with extension *.text*. For instance, *test1.test* and *test2.test* are valid names for these files.

Once your test files are written, you can launch the test with the command-line tool *test_task* from the INGInious distribution, with the following calling syntax :
::
    test_task [-v|--verbose] task_folder
    
where *verbose* is used to print the complete standard output produced by the execution of your task and *task_folder* is the folder which contains the task files (please note that the *.task* file associated with the task must be found in the parent directory).
