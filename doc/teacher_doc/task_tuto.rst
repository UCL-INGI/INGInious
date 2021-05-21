Tutorial
========

In this document we will describe how to create a simple task, that checks that a code in Python returns "Hello World!".

.. note::

    Demonstration tasks are made available for download on the `INGInious-demo-tasks repository <https://github.com/UCL-INGI/INGInious-demo-tasks>`_. They
    can also be downloaded and installed automatically via the :ref:`inginious-install` script. You can also download courses examples on the marketplace page which allows to easily import courses files. The list of these open source courses is also available on the `INGInious-courses repository <https://github.com/UCL-INGI/INGInious-courses>`_
	

Creating the task description
-----------------------------

Using the webapp
````````````````

If you are using the webapp, this procedure can be done using the graphical interface:

#. Go to the *Course administration/Tasks* page, enter ``helloworld`` as a new task id and click on *Create new task*.
#. In the *Basic settings* tab, set the task name to ``Hello World!`` and put some context and author name. Container
   setup can be left with default parameters.
#. In the *Subproblems* tab, add a new *code*-type problem with problem id ``question1``.
#. Set some problem name and context, and set language to ``python``.
#. Save changes and go to *Task files* tab.

Manually
````````
This is only possible if the administrator has given access to the course directory to the course administrator.

The task description is a YAML file describing everything that INGInious needs to know to verify the input of the student.
Here is a simple task description. Put this file with the name ``task.yaml`` in a newly created ``helloworld`` folder in
your course directory.

.. code-block:: yaml

    author: "The INGInious authors"
    accessible: true
    name: "Hello World!"
    context: "In this task, you will have to write a python script that displays 'Hello World!'."
    problems:
        question1:
            name: "Let's print it"
            header: "def func():"
            type: "code"
            language: "python"
    limits:
        time: 10
        memory: 50
        output: 1000
    environment: default

Most of the fields are self-explanatory. Some remarks:

- The field ``problems`` is a dictionary of problems. Each problem must have an unique id, for example here ``question1``.
- Problem ``question1`` have its ``type`` field that equals to ``code``, which means the student must enter some code
  to answer the question. Other types exists, such as multiple-choice.
- The field ``limits`` are the limits that the task cannot exceed. The ``time`` is in seconds, and ``memory`` and
  ``output`` are in MB.
- The ``environment`` field is intended to change the environment where the tasks run. The available environments are
  those you downloaded during installation or those you created by creating a grading container.
  Please see :doc:`create_container`.

More documentation is available here: :doc:`task_file`.

Creating the run file
---------------------

In your task folder, you will put every file needed to test the input of the student. This folder content can be shown
in the webapp in the *Task files* tab of the *Edit task* page.

#. Create a template file ``template.py``, where we will put the code of the student.
   ::

       def func():
           @    @question1@@

           func()

   The syntax is very simple: put a first ``@`` on the line where you want to put the code of the student.
   Then indent the line and write a second ``@``. Now write the problem id of the problem you want to take the input
   from (``question1``) then write another ``@``, write a possible suffix (not used here), and then finish the line
   with a last ``@``.

#. Create the ``run`` file. This file will be the script that is launched when the task is started. Here we will create
   a *bash* script, that parses the template and verifies its content.

   .. code-block:: python

        # This line parses the template and put the result in studentcode.py
        parse_template("template.py", "student/studentcode.py")

        # Verify the output of the code... (we ignore stderr and retval here)
        output, _, _ = run_student_simple(python student/studentcode.py)

        if output == "Hello World!":
            # The student succeeded
            set_global_result("success")
            set_global_feedback("You solved this difficult task!")
        else:
            # The student succeeded
            set_global_result("failed")
            set_global_feedback("Your output is " + output)

   Here we use four commands provided by INGInious, ``parse_template``, ``run_simple``,
   ``set_global_result`` and ``set_global_feedback``.
   The code is self-explanatory; just notice the usage of ``run_student_simple`` (a version of `run_student`) that ask INGInious
   (precisely the Docker agent) to start a new *student container* and run inside the command ``python studentcode.py``.

   Please note that the ``run_student_simple`` command is fully configurable: you can change the environment on which you run
   the task, define new timeouts, memory limits, ... See :ref:`run_student` for more details.

#. If not using the webapp, don't forget to give the ``run`` file the execution rights:
   ::

      $ chmod +x helloworld/run


More documentation is available here: :doc:`task_file`.
