.. _inginious-autotest:

inginious-autotest
==================

Assistant to test automatically the content and the format of the ``task.yaml`` files of a courses and to check if the output of the ``submission.test`` files corresponding to submissions with the new test is consistent with the output of the test in the inginious instance.

The ``submission.test`` files for a task are situated in a ``test/`` folder which is a sub directory of the task directory and which at the same level as the ``task.yaml``.

.. program:: inginious-autotest

::

    inginious-autotest [-h] [--logging] [-f FILE] [--ptype PTYPE [PTYPE ...]] task_dir course_dir

.. option:: -h, --help

   Display the help message.

.. option:: --logging

   Activate the logging of the used inginious backend and docker agent

.. option:: -f FILE

    Write the output in a json format in the specified file in case of failure

.. option:: --ptype PTYPE [PTYPE ...]

    Specify additional problem types to be used.

.. option:: task_dir

    Path to the courses directory of inginious, corresponds to field task_directory in the ``configuration.yaml``

.. option:: course_dir

    Path to the course directory to test

