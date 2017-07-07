.. _run_file:

Run file
========

When the student have submit his/her code, INGInious starts a new Docker container
with the right *environment* for the task (as given in the *.task* file). Inside this
container is launched a script, called *run*, that you have to provide in the
directory of your task.

Here is a simple example of a *run* file, compatible with the *default* environment,
that simply returns that the student's code is OK:
::

    #!/bin/bash
    feedback-result success

The *run* script is simply an executable application (a bash script, a python script, or
a compiled executable runnable by the container). INGInious' default containers provides
commands (also available as python libraries) to interact with the backend.

By default, the script is run inside the container in the /task directory, by a non-root
user. You can modify the container to change this (and everything else).

Feedback commands
-----------------

feedback-result
```````````````
The *feedback-result* command sets the submission result of a task, or a problem,
and uses the following syntax :

::

    feedback-result [-i|--id PROBLEM_ID] RESULT

The execution result can be of different types:

- success : the student succeeded the task
- failed : there are error in the student answer
- timeout : the tests timed out
- overflow :there was a memory/disk overflow
- crash : the tests crashed

For instance, the following command will inform that the student succeeded:

::

    feedback-result success

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import feedback
    feedback.set_global_result("success") # Set global result to success
    feedback.set_problem_result("failed", "q1") # Set 'q1' subproblem result to failed

feedback-grade
``````````````
The *feedback-grade* command sets the submission grade and uses the following syntax:
::

    feedback-grade GRADE

If no grade is specified, the result score will be binary. This means that a failed
submission will give a 0.0% score to the student, while a successful submission will
give a 100.0% score to the student. For instance, the following command will give
an 87.8% grade to the student:

::

    feedback-grade 87.8

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import feedback
    feedback.set_grade(87.8) # Set the grade to 87.8%

feedback-msg-tpl
````````````````

The *feedback-msg-tpl* sets the feedback message associated to the task or a subproblem, using a `Jinja2 <http://jinja.pocoo.org/docs/2.9/>` template.

It needs the name of a template. The command attempt to use a translated version of the template first; given that you give TPLNAME as first
argument to the command, *feedback-msg-tpl* will attempt to find the template, by search in this order:

- `[local_dir]/TPLNAME.XX_XX.tpl`
- `[task_dir]/lang/XX_XX/TPLNAME.tpl` (preferred way)
- `[local_dir]/TPLNAME.tpl`

Once found, the template is parsed using `Jinja2 <http://jinja.pocoo.org/docs/2.9/>`, which allows you to send parameters to the template.
These parameters should be given in the command line, in the form `name=value`:

::

    feedback-msg-tpl TPLNAME option1=value1 option2=value2

Inside your template, you can use these parameters like this:

::

    Option 1 was {{ option1 }} and the option 2 was {{ option 2 }}

Which will return

::

    Option 1 was value1 and the option 2 was value2

See the Jinja2 documentation to discover all possibilities.

Your template must return a valid RestructuredText.

Optional parameters:

-a, --append                        append to current feedback, if not specified, replace the
                                    current feedback.
-i, --id PROBLEM_ID                 problem id to which associate the feedback, leave empty
                                    for the whole task.

feedback-msg
````````````
The *feedback-msg* command sets the feedback message associated to the task or a subproblem. It has several
optional parameters:

-a, --append                        append to current feedback, if not specified, replace the
                                    current feedback.
-i, --id PROBLEM_ID                 problem id to which associate the feedback, leave empty
                                    for the whole task.
-e, --escape                        interprets backslash escapes
-m, --message MESSAGE               feedback message

If the message is not specified, the feedback message is read from stdin. For instance, the command can be
used as follows:

::

    feedback-msg -ae -m "This is the correct answer.\n\nWell done!"

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import feedback
    feedback.set_global_feedback("Well done !") # Set global feedback text to `Well done !`
    feedback.set_problem_feedback("This is not correct.", "q1") # Set 'q1' problem feedback to `This is not correct.`

.. _feedback-custom:

feedback-custom
```````````````
The *feedback-custom* command sets a pair of key/value custom feedback, mainly used with plugins,
and uses the following syntax :

::

    feedback-custom [-j|--json] key value

The ``--json`` parameter indicates if ``value`` must be parsed as a JSON string.
Please refer to the plugin documentation to know which value you have to set for ``key`` and ``value`` parameters.

For instance, the following command set the value ``56`` to the ``score`` key:

::

    feedback-custom score 56

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import feedback
    feedback.set_custom_value("score", 56) # Set the `score` key to value 56

reStructuredText helper commands
--------------------------------

Several helper commands are available to format the feedback text, which format is reStructuredText.

rst-code
````````

The *rst-code* command generates a code-block with the specified code snippet and language
to enable syntax highlighting. It has the following parameters:

-l, --language LANGUAGE    snippet language, leave empty to disable syntax highlighting
-e, --escape               interprets backslash escapes
-c, --code CODE            snippet code

If the code parameter is not specified, it is read on standard input. The result is written on standard output.
For instance, the command can be used as follows:

::

    cat test.java | rst-code -l java | feedback-msg -a

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import rst
    codeblock = rst.get_codeblock("java", "int a = 42;") # Java codeblock with `int a = 42;` code
    feedback.set_global_feedback(codeblock, True) # Appends the codeblock to the global feedback

rst-image
`````````

The *rst-image* command generates a raw reStructuredText block containing the image to display. It has the
following syntax

::

    rst-image [-f|--format FORMAT] FILEPATH

The optional *format* parameter is used to specify the image format (jpg, png,...) if this is not explicitly specified
the the image filename. The output is written on the standard output. For instance, the command can be used as follows:

::

    rst-image generated.png | feedback -a

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import rst
    imgblock = rst.get_imageblock("smiley.png") # RST block with image
    feedback.set_global_feedback(imgblock, True) # Appends the image block to the global feedback


rst-msgblock
````````````
The *rst-msgblock* command is used to generate a reStructuredText admonition in a specific colour according to the
message type. It has the following optional parameters:

-c, --class CSS_CLASS    Bootstrap alert CSS class:

                          - success
                          - info
                          - warning
                          - danger
-e, --escape             interprets backslash escapes
-t, --title TITLE        message title
-m, --message MESSAGE    message text

If the message parameter is not set, the message is read from standard input. For instance, the command can
be used as follows:

::

    rst-msgblock -c info -m "This is a note" | feedback -ae

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import rst
    admonition = rst.get_admonition("success", "Yeah!", "Well done!") # RST message block of class "success" and title "Yeah!"
    feedback.set_global_feedback(admonition, True) # Appends the block to the global feedback

rst-indent
``````````
The *rst-indent* command is used to handle the indentation of the given text. It has the following optional arguments:

-e, --escape                      interprets backslash escapes
-c, --indent-char INDENT_CHAR     indentation char, default = tabulation
-a, --amount AMOUNT               amount of indentation, default = 1
-m, --message MESSAGE             message text

If the message parameter is not set, the text is read from standard input. The amount of indentation can be negative
to de-indent the text. For instance, the command can be used as follows, to add an image to the feedback,
inside a list item, for instance :

::

     rst-image generated.png | rst-indent | feedback -a

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import rst
    rawhtml = rst.indent_block(1, "<p>A paragraph!</p>", "\t") # Indent the HTML code with 1 unit of tabulations
    feedback.set_global_feedback(".. raw::\n\n" + rawhtml, True) # Appends the block to the global feedback

Input commands
--------------

getinput
````````

The *getinput* command returns the input given by the student for a specific problem id.
For example, for the problem id "pid", the command to run is:
::

    getinput pid

When a problem is defined with several boxes, the argument becomes *pid/bid* where "pid"
stands for the problem id and "bid" for "box id". If the problem is a file upload, the problem id can be appended
with ``:filename`` or ``:value`` to retrieve its filename or value.

Note that *getinput* can also retrieve the username/group of the user that submitted the task. You simply have to run
::

    getinput @username

If the submission is made as a user, it will contain the username. It it's made as a group,
it will contain the list of the user's usernames in the
group, joined with ','.

The four letter code of the student's language (for example `en_US` or `fr_FR`) can also be retrieved using
::

    getinput @lang

Note that plugins are free to add new `@`-prefixed fields to the available input using the `new_submission` hook.

**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import input
    thecode = input.get_input("q1") # Fetch the code for problem `q1`


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
    @        @problem_one@@
        }
    }

To access the filename and text content of a submitted file, the *problemid* can be
followed by a *:filename* or *:value* suffix.


**In Python** : the equivalent command can be directly obtained with:

.. code-block:: python

    from inginious import input
    thecode = input.pasrse_template("student.c") # Parse the `student.c` template file
    thecode = input.pasrse_template("template.c", "student.c") # Parse the `template.c` template file and save the parsed file into `student.c`

.. _run_student:

run_student
-----------

*run_student* allows the *run file* to start, at will, sub-containers. This makes you able to secure the grading,
making sure the untrusted code made by the student don't interact with yours.

The sub-container is launched with a different user who has read-write accesses to the task ``student`` 
subdirectory. Only the changes made in that directory will remain in the main container.

*run_student* is fully configurable; you can change the container image (environment), set new timeouts, new memory
limits, ... And you can call it as many time as you want.

--container CONTAINER             Name of the container to use. The default is the same as the current container.
--time TIME                       Timeout (in CPU time) for the container. The default is the same as the current container.
--hard-time TIME                  Hard timeout for the container (in real time). The default is three times the value indicated for --time.
--memory MEMORY                   Maximum memory for the container, in Megabytes. The default is the same as the current container.
--share-network                   Share the network stack of the grading container with the student container. This is not the case by
                                  default. If the container container has network access, this will also be the case for the student!

Beyond these optionals args, *run_student* also takes an additional (mandatory) arguments: the command to be run in the new container.

More technically, please note that:

- *run_student* proxies stdin, stdout, stderr, most signals and the return value
- There are special return values:
    - 252 means that the command was killed due to an out-of-memory
    - 253 means that the command timed out
    - 254 means that an error occurred while running the proxy

archive
-------

*archive* allows you to put some data in an archive that will be returned to the frontend
and stored in the database for future reading. You can put there debug data, for example.

The command takes some arguments, which are all optional:

-o, --outsubdir DIRECTORY           will put the file (specified with -a or -r)in the
                                    specified sub-directory in the output archive
-a, --add FILEPATH                  add the file to the archive
-r, --remove FILEPATH               remove the file from the archive

Obsolete commands
-----------------

feedback (obsolete since v0.4)
``````````````````````````````

The *feedback* command allows you to set the result of your tests.
Every argument is optional.

-r, --result STATUS            set the result to STATUS. STATUS can be
                               - success (the student succeeded the task),
                               - failed (there are error in the student answer),
                               - timeout (the tests timed out),
                               - overflow (there was a memory/disk overflow) or
                               - crash (the tests crashed)
-e, --escape                   interprets the space-like escape chars.
-f, --feedback MSG             set the feedback message to MSG. It is possible to set different
                               messages for each problems. You can use *-i* to change the problem
                               to which you assign the message
-i, --id PROBLEMID             set the problem id to which the message from the *-f* option is
                               assigned. Unused if *-f* is not set.
-g, --grade GRADE              the grade. Should be a floating point number between 0(no points) and
                               100(all points) (bonuses, up to 200, are allowed).
-c, --custom CUSTOM            add a value VAL to the "custom" dictionnary, with key KEY, where CUSTOM is ``KEY:VAL``, which is stored in DB.
                               Useful for plugins.
-j, --custom-json CUSTOM   same as ```--custom``` but VAL is a json-encoded dictionnary

The *feedback* command can be called multiple times.

::

    feedback --result success --feedback "You're right, the answer is 42!"
