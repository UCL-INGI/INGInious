inginious-test-task
===================

Test you task inside a docker container on your local machine, and gives you access to it.
Allows to manually test your tasks in the exact same environment as a real INGInious instance would do, but with direct shell access to do trial
and error in an efficient way.

One limitation though: ``inginious-test-task`` cannot execute the internal command ``run_student``.

.. program:: inginious-test-task

::

    inginious-test-task [-h] [--testdir TESTDIR] task container

.. option:: -h, --help

   Display the help message.

.. option:: --testdir TESTDIR

   Specify in which directory the files needed for running the container will be created. See test_task_tutorial_ for more informations.
   By default, it is ``./``

.. option:: task

   The task directory to test

.. option:: container

   Name of the container image to run. Usually in the form ``ingi/inginious-c-***``. For example, ``ingi/inginious-c-default``.
   All the default containers are available on the `UCL-INGI page from Docker Hub`_.

.. _UCL-INGI page from Docker Hub: https://hub.docker.com/u/ingi/

.. _test_task_tutorial:

Tutorial
--------

Let's say you a written a task in Java. Here is how to debug your task:

1.  Create somewhere a test directory
2.  Run

    ::

        inginious-test-task /path/to/your/task/dir ingi/inginious-c-java8scala

    We use here ``ingi/inginious-c-java8scala`` here because it is a Java task. See the `UCL-INGI page from Docker Hub`_ for more containers.
3.  The tool will start and show something like

    ::

        ----------------------------------------------------------

        Put your input for the task in the folder ./tests/0/input.
        They will be available via the commands getinput and parsetemplate inside the container.
        The output of the container will be available in the folder ./tests/0/output.
        The archive made via the `archive` command inside the container are available in the folder ./tests/0/archive.

        I will now start the container.

        ----------------------------------------------------------
        [root@679f6118f8a7 task]#

    As indicated, the tool have created a new directory ``./tests/0`` (if you re-run the tool in the same dir, it will become ``./tests/1`` and so
    on). Inside this directory, there are some directories and files:

    * ``feedback.yaml``: contains the feedback that you is set inside the container. For now, it should be empty.
    * ``input/``: contains, for each problem id, a file with the name of the problem id. Putting text inside these file will make them available
      for the command ``getinput`` and ``parsetemplate`` inside the container.
    * ``output/``: contains the output of the ``archive`` command, among others
    * ``task/``: contains a *copy* of the original task directory. It is directly available from the container, and change are mirrored.
    * ``tests/``: tests made with the ``test`` command inside the container are put here.

    The command also gave you a bash access inside the container. You can do everything inside, from calling ``yum`` to running ``./run``.

    That's all you need to know. Let's continue the demo anyway.
4.  Let's say you have a problem id named ``helloworld``. Edit the file ``./tests/0/input/helloworld`` and put ``something`` inside.
5.  Now, run ``getinput helloword`` inside the container. ``something`` should appear on the screen.
6.  You can also run ``feedback -r success``. See how the file ``feedback.yaml`` changed.
7.  You can run your ``run`` file by simply putting ``./run`` inside the container.
8.  Exit the container by calling ``exit``.
