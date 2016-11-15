.. _inginious-test-task:

inginious-test-task
===================

Replay a task with the set of *.test* files available in the task folder and checks if results are identical. If results
differ, detailed information are printed on the terminal.

The *.test* files can be obtained by downloading a valid submission and storing the *.test* file found in the downloaded
archive in the task folder.

.. program:: inginious-test-task

::

    inginious-test-task [-h] [-c CONFIG] [-v] courseid taskid

.. option:: -h, --help

   Display the help message.

.. option:: -c, --config

   Specify the INGInious config file to use. If not specified, looks for a configuration file in the current directory

.. option:: -v, --verbose

   Increase output verbosity: display entire stdout/stderr.

.. option:: courseid

    The course id corresponding to the task to test.

.. option:: taskid

    The task id corresponding to the task to test.
