Random tasks parameters
=======================

Typical INGInious tasks are displayed the same way for all the students.
However, it is possible to display some parameters randomly for students to
avoid copy/pasting their peers submissions.
This can, for instance, be a numerical value for a computation, or the name of a
variable.

INGInious allows you to generate one or several random numbers that are stored in
database per student. To enable this, specify the number of random numbers
(of parameters) you need in the task editor *Basic settings* tab. By default,
the same set of random numbers is kept per student. If you want to generate random
numbers each time the student opens the task, check the *Regenerate random input* box.

Accessing the task random parameters
------------------------------------

The random numbers generated for the task are accessible through the webapp as
well as in the INGInious container and run file.

Through the webapp
``````````````````

Several context-specific inputs are accessible through a ``input`` Javascript dictionary
in the task and subproblems context.

.. code-block:: Javascript

    var input = {
        "@lang": "fr",
        "@username": "foobar",
        "@random": [0.9805443622648311, 0.8755252481699163],
        "@state": ""
    }

The ``@random`` key contains the random number list. In order to use it,
declare a ``..raw:: html`` directive in your contexts and include
some Javascript code via the HTML ``<script>`` tag.

Through the container
`````````````````````

The random number list can be accessed using the ``getinput`` API with the specific
id ``@random``.

Using the shell API:

.. code-block:: bash

    getinput @random

Using the Python API:

.. code-block:: python

    from inginious import input as inginious_input
    random_list = inginious_input.get_input("@random")
