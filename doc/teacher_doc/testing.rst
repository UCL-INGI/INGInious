Debugging tasks
===============

There are different ways to get more insight on what's going wrong with your tasks in case
of errors. Generally, those errors come from the fact the running environment may be different
from your task development environment (OS configuration, software set,...).

Debug information
-----------------
Every time an administrator submit a new job and receives result on the frontend, a *Debug information*
is made available in the sidebar. Those information contain all the submission metadata (input, result,
feedback,...) as well as the grading container standard output and standard error output.

Please note that every manipulation done with those streams will not be visible anymore in those information.
Redirected output won't be shown. This is important as spawning processes in non-shell oriented languages
will not redirect the spawned process standard output on the grading container standard output.

SSH debug
---------
Debugging tasks is made more easy using SSH debug feature. This aims at providing the same
user experience as local development. To make this feature work remotely
(regarding the INGInious Docker agent), please make sure you've correctly set up the debug
hosts and ports (see :ref:`ConfigReference` if needed).

Every administrator is able from the frontend to launch a debugging job. This is done by clicking
on the *>_* (left-chevron, underscore) button next to the *Submit* button. According to your
configuration, either a SSH command-line with auto-generated password will be given you (you will,
in this case, need an SSH client installed), or an embedded SSH console will pop up as the
feedback position.

Unit-tests on tasks
===================

It may sometimes be useful to check that your changes does not affect the way previous
submissions are graded. You can test your tasks thanks to several tools included in
the default INGInious environment. Almost everything can be tested :

- Standard output given by the execution of your task
- Main result returned for a given set of inputs (success, or failed)
- Feedbacks given to the students
- User-defined pairs of tag and value

Tests can be described with test files, as described below.

Defining a new unit test
------------------------
If you want to test your own assertions, you can use the tool
``definetest`` in your task code. This command must be called with the
following syntax :

::

    definetest key value

where ``key`` is a tag, or an identifier, which will refer to the ``value``
you want to test at a given execution point. The *value* argument is of
type string.

Creating a new test file
------------------------
Now you've defined some tags for which you want to assert the value
correctness, you can define some test files. These must be written in
YAML with the following syntax. It must be like this :

::

    input:
        pid_1:"Answer to the problem with problem id pid_1"
        pid_2:"Answer to the problem with problem id pid_2"
    result:"success"
    tests:
        answer:"42"

In this example, ``pid_1`` and ``pid_2`` are two given problem id, which you
defined in your task file. The value associated with theses keys are the
input you would insert in the form field.

In this file, only the final result and the value of test tag ``answer``
are wanted to be checked with the specified expected values. More fields
can be checked :

- ``result`` : the result of the execution of your task
- ``text`` : the general feedback given to the student
- ``stdout`` : the standard output produced by the execution of your task
- ``problems`` : a YAML entry containing pairs of problem identifiers and
  expected feedback
- ``tests`` : a YAML entry containing pairs of test tags and expected
  values

Not specified fields won't be checked during the testing process. So if
you don't want to test the correctness of your standard output or
feedback, just omit these fields in the expected output file.

Generated test files
--------------------
Tests files are automatically generated with each submission, and are
included in the downloadable archive with the extension *.test*.
This can avoid spending much time on writing them as they are
YAML-formatted input/output internally used by INGInious.
This way, you can write the tests from the INGInious frontend, or even
use the submissions made by students to improve you tests suite and/or
to fix your bugs.

Automatically generated test files contain more information than
required by the description given above. These information are for
internal INGInious usage and can be ignored and removed from the files.

Automated tests with *.test files
---------------------------------

To test your task, you need to put your tests files together in the task
directory with extension *.test*. For instance, *test1.test* and
*test2.test* are valid filenames.

Once your test files are written, you can launch the test with the
command-line tool :ref:`inginious-test-task`.
