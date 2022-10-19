.. _inginious-task-test:

inginious-task-test
==================

This tool replays submissions of a given course to ensure that its task's grading processes 
are consistent over time. 

The verification of a specific task may be skipped by adding a ".testignore" file in the task 
directory.

.. program:: inginious-task-test

::

    inginious-task-test [-h] [-c CONFIG] [-v] [-p [PLUGINS ...]] courseid [taskids ...]

.. option:: -h, --help

   Display the help message.

.. option:: -c CONFIG, --config CONFIG

   Path towards the INGInious instance configuration file.

.. option:: -v, --verbose

   Display more output.

.. option:: -p [PLUGINS ...], --plugins [PLUGINS ...]

   Additional plugins required to replay the course's tasks.

.. option:: courseid

    Course ID of the course to test, e.g., linfo1140. It should match the name of the corresponding
    course directory in the ``tasks`` directory.

.. option:: taskids

    If specified, a list of tasks to test. If none is given, all the task of the course are replayed.
