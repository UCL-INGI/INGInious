INGInious as a grader for edX
=============================

Configuration of the edX plugin
-------------------------------

First thing to do is to add the configuration for the plugin, in configuration.yaml:

::

    plugins:
      - plugin_module: frontend.plugins.edx,
            courseid: "LouvainX",
            page_pattern: "/grader"

``courseid``
	courseid is the id of the course that you want to provide to edX.
	(Please note that you can have multiple instances of the edX plugin, allowing you to use it for more than one course)
``page_pattern``:
	pages that will lead to the edX grader. Can be a simple string or a regex. Note that if you use multiple edX plugin instances,
	page_patterns have to be unique.

Once this is done, a basic POST interface will be available at yourip:port/grader. This also provides a simple debugging console (with *not* working
examples).

Asking people at edX to create a queue for your course
------------------------------------------------------

Next step is to send a mail to your contact person at edX, asking kindly to add a *passive* grader with the URL "yourip:port/grader".
Once this is done, the edX team will give you a "queue name".

Creating tasks for your edX course
----------------------------------

Tasks for edX courses are (more or less ;-)) the same as normal tasks for the frontend.
Two things to remember: there can be only one subproblem, of type code, and its problem_id has to be "student_response".

Here is an example of task.yaml for the C# test task:
::

    accessible: true
    author: Guillaume Derval
    name: C# Hello World
    context: |-
        A context that is not used by edX but that is shown in the frontend of INGInious
        (NB: will be used by edX after the next release of INGInious, see bottom of the page)
    environment: mono
    limits:
        memory: '100'
        time: '30'
        output: '2'
    problems:
        student_response:
            type: code
            header:  |-
                A context that is not used by edX but that is shown in the frontend of INGInious
                (NB: will be used by edX after the next release of INGInious, see bottom of the page)
            name: "the same remark goes for this field"
            language: csharp

And the corresponding "run" file:
::

    #! /bin/bash

    # Put the input of the student inside test.cs
    getinput student_response > test.cs

    # Compile test.cs
    mcs test.cs &> compilation.log
    if [ $? -ne 0 ]; then
        printf 'There was an error while compiling you code\n\n::\n\n' > temp.log
        cat compilation.log | awk '{printf "\t%s\n", $0}' >> temp.log
        feedback --result failed --feedback "$(<temp.log)"
        exit 0
    fi

    # Verify the output of the code...
    output=$(mono test.exe)
    if [ "$output" = "Hello World!" ]; then
        # The student succeeded
        feedback --result success --feedback "You solved this difficult task!"
    else
        # The student failed
        feedback --result failed --feedback "Your output is $output"
    fi

Adding the task to edX
----------------------

Next, and final step, is to add the task to your course on edX.
Connect to the studio, and create a custom exercice, and copy-paste this XML:

::

    <problem>
        <text>
            Enter here some context for the problem
        </text>
        <coderesponse queuename="YOUR_QUEUE_NAME">
            <textbox rows="10" cols="80" mode="csharp" tabsize="2"/>
            <codeparam>
                <initial_display/>
                <grader_payload>{"tid": "THE_TASK_ID"}</grader_payload>
                <answer_display/>
            </codeparam>
        </coderesponse>
    </problem>

Fill the correct queue name and task id, write some context for the task (or copy/paste the one you put in the task.yaml), and save.
Click on preview, it should work!

Current and future way of working
---------------------------------

For now, INGInious is provided with a simple plugin that is a *passive* grader for edX XQueue.
While this is the simplest implementation possible (< 100 lines of codes), this also comes with some drawbacks:

- Only one input field per exercise
- maximum 30 seconds to give the grading result to edX (limits greatly some courses with heavy tasks)
- Bad syntax highlighting
- Duplicate code for the context of the exercise (that should be indicated in edX and in INGInious if you really use the frontend)
- Need to ask the edX team to create a queue for you, as there is no public interface for this

We are going (in a near future = this summer 2015) to replace this method with an integration of the LTI_ specification, which resolves all these
small drawbacks.

.. _LTI: http://www.imsglobal.org/lti/index.html