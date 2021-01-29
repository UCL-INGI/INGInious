Exercises
=========

INGInious proposes by default several types of exercises. This lets teachers make various exercises and diversified course.
Those types can be Code and Single line code, Multiple choices, File upload or Match.

Every type of exercise must implement Problem class which is the basic problem class. This class defines some abstract methods that will be overwritten in the different types of exercise.

They all defined the ``check_answer`` method that should return True if the answer is valid, False if not and None if the check must be done in a virtual machine.

Problem types
-------------

Code and Single Line Code
^^^^^^^^^^^^^^^^^^^^^^^^^

Those are present together as Single Line Code is a child class of Code problem.
Both took code as input which can be use after by the teacher through the run file.
They both defined there ``check_answer`` method with the None value as the code must be send to a virtual machine.

File upload
^^^^^^^^^^^

This problem takes a file as input. The ``check_answer`` method also return a None value to let the teacher run specific test through the virtual machine.
Two specific properties are also defined to limit file extensions and file size.

Multiple choices
^^^^^^^^^^^^^^^^

This classical multiple choices problem defines the most basic exercise type. It takes the selected answer(s) and calculate validation immediately (no virtual machine needed).

Match
^^^^^

This problem type simply verify that expected value and answer are strictly equal.


Custom exercises definition
---------------------------

As previously said, it is possible to define custom problem by implementing the Problem class.
This will require some method to implement to define the behavior of the custom problem.
The most effective way to add your custom type is to do it in a `plugin <https://inginious.readthedocs.io/en/latest/dev_doc/plugins.html>`_.


Problem display
---------------

Once your problem is defined, you'll probably need to display this in the frontend.
Like the Problem implementation, all you have to do is to define your own class that implements ``DisplayableProblem``.
This class is available only in the frontend as this is only use by the frontend.
By writing custom edit box and input, you'll be able to define your own problem input.