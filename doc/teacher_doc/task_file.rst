.. _task.yaml:

Task description files
======================

Inside a course folder (see :ref:`course`), tasks are identified by subdirectories named by their task id and containing
a ``task.yaml`` file. For instance, this file, for a task with id ``taskid1``, should be placed in a ``taskid1``
subdirectory.

``task.yaml`` is a YAML file containing information about the task.

.. code-block:: yaml

    author: Your name
    contact_url: mailto:yourself@example.com?subject=About the task {task_id} (course {course_id}), INGInious username {username}
    context: |-
        The context of this task. Explain here what the students have to do.
    order: 1
    groups: false
    name: The complete name of this task
    accessible: true
    problems:
        a_problem_id:
            name: The title of this question
            header: A header for this question
            type: code
            language: c
    limits:
        time: 30
        memory: 128
    environment: default
    network_grading: False


-   ``author``, ``context``, ``order``, ``name``, ``language`` and ``header`` are only needed
    if you use the frontend.
    ``context`` and ``header`` are parsed using restructuredText.

-   ``contact_url`` is an url to contact the maintainer of the task. It is a Python format string that will be formatted with values for the keys ``{task_id, course_id, username}``. It must form a valid URL. It can thus also be an HTTP link.

-   ``order`` is an integer, used by the frontend to sort the task list. Task are sorted
    in increasing value of *order*.

-   ``weight`` is a decimal value indicating the weight of the task score to use to compute the total course score.

-   ``accessible`` describes when the task is accessible to student. This field is not
    mandatory (by default, the task is visible) and can contain the following values:

    ``true``
        the task is always accessible
    ``false``
        the task is never accessible
    ``"START"``
        where *START* is a valid date, like "2014-05-10 10:11:12", or "2014-06-18".
        The task is only accessible after *START*.
    ``"/END"``
        where *END* is a valid date, like "2014-05-10 10:11:12", or "2014-06-18".
        The task is only accessible before *END*.
    ``"START/END"``
        where *START* and *END* are valid dates, like "2014-05-10 10:11:12", or
        "2014-06-18". The task is only accessible between *START* and *END*.
    ``"START/SOFT_DEADLINE/END"``
        where *START*, *SOFT_DEADLINE* and *END* are valid dates, like "2014-05-10 10:11:12",
        or "2014-06-18". The task is only accessible between *START* and *END*, but the
        publicly communicated end time is *SOFT_DEADLINE*.

-   ``problems`` describes sub-problems of this task. This field is mandatory and must contain
    at least one problem. Problem types are described in the following section
    `Problem types`_. Each problem must have an id which is alphanumeric and unique.

-   ``limits`` contains the limits that will be applied on the grading container. ``time``
    is the CPU timeout in seconds, and ``hard_time`` is the timeout in real time.
    
    By default, ``hard_time`` is defined to be to 3*``time``. This can leads to problems
    when INGInious is under heavy load, but allow to detect processes that do too much system
    interruptions (sleep calls or IO)
    
    ``memory`` is the maximum memory allowed to the container.
    
    Please note that the limits of the student containers (container that you start inside
    the grading container) will use these limits by default.
    
-   ``environment`` is the name of the Docker container in which the grading code will run.
    This field is only needed if there is code to correct; a multiple-choice question does
    not need it. This environment will be used by default for the student containers.

-   ``groups`` allows to indicate if the submission is to be done individually or per groups.
    (see Groups).

-   ``network_grading`` indicates if the grading container should have access to the net. This
    is not the case by default.

-  ``evaluate`` indicates the submission that must be used for evaluation. This can be either:

   ``best``
       This is the default value. In this case, the best submission is used.
   ``last``
       In this case, the last submission is used.

- ``submission_limit`` indicates the amount of submissions a student can make within a certain period of time.
  It is composed of two fields:

  - ``amount`` is an integer value indicating the amount of submission. A value of ``-1`` corresponds to an infinite
    amount of submissions.
  - ``period`` is an integer value indicating the length of the submission period in hours. A value of ``-1`` corresponds
    to an infinite period. At the end of this period, the student can submit ``amount`` submissions again during
    ``period`` hours.

- ``stored_submissions`` indicates the amount of submissions that must be saved in the submission history. A value of
  ``0`` keeps all the submissions.

Problem types
-------------

Code problems
`````````````

``type: code`` problems allows students to submit their code. The code is then
sent to a container where a script, made by the teaching staff, corrects it.

Here is a simple example for a code problem

.. code-block:: yaml

    type: code
    language: c
    header: |-
        Hello dear student!
        I'm a multiline header!
    name: A name
    optional: false

*header* and *language* are only needed when using the frontend and are not mandatory.
This description typically displays on the frontend a box where student
can put their code.

*optional* is an optional field, that defaults to false, that indicates if this problem is mandatory or not.

Code problem input's are available in the *run* script (see :doc:`run_file`) directly with the
id of the problem.

Single code line problems
`````````````````````````

``type: code_single_line`` is simply a code box that allows a single line as input.

.. code-block:: yaml

    type: code_single_line
    language: c
    header: |-
        Hello dear student!
        I'm another multiline header, parsed with *RST*!
    name: Another problem
    optional: false


Single line code problem input's are available in the *run* script (see :doc:`run_file`) directly with the
id of the problem.

Advanced code problem
`````````````````````

Advanced code problems are available:

.. code-block:: yaml

    type: code
    header: some text
    name: And again, another name
    boxes:
        boxId1:
            type: text
            content: Some additional text
        boxId2:
            type: input-text
            maxChars: 10
            optional: true
        boxId3:
            type: multiline
            maxChars: 1000
            lines: 8
            language: java

*Boxes* are displayable (on the frontend) input fields that allows the student
to fill more than one entry per problem. Different box types are available, all of them
are demonstrated above. Every configuration in the boxes (*maxChars*,*lines*,*language*)
is not mandatory, except *content* if the box type is *text*, and the field *optional* (default to false),
that indicates if the box is mandatory or not.

In the *run* file (see :doc:`run_file`), boxes input are available with the name
*problem_id/box_id*

Match problems
``````````````

Match problem are input that allows a single-line input from the student and that
returns if the student entered exactly the text given in the "answer" field.

.. code-block:: yaml

    name: The answer
    type: match
    header: some text describing this problem
    answer: 42

Match problem input's are available in the *run* script (see :doc:`run_file`)
directly with the id of the problem.

Multiple choice problems
````````````````````````

.. code-block:: yaml

    name: An exercice
    type: multiple_choice
    header: The answer to life, the universe and any other things is
    multiple: true
    limit: 2
    error_message: "Wrong answer. Don't panic, and read Hitchhiker's Guide to the Galaxy."
    success_message: "You're right! But don't forget to always take your towel with you."
    choices:
      - text: It is, of course, 42!
        valid: true
      - text: It should be *42*
        valid: true
      - text: 43!
        feedback: "43 isn't the answer. Maybe can you try to substract one?"
      - text: 41?
        feedback: "41 isn't the answer. Maybe can you try to add one?"

Choices are described in the ``choices`` section of the YAML. Each choice must have
a ``text`` field (on the frontend) that will be parsed in restructuredText. Valid choices
must have a ``valid: true`` field. The field ``feedback`` is a message that will be displayed
when the student check the choice.

``multiple`` indicates if the student may (or not) select more than one response.

Choices are chosen randomly in the list. If the ``limit`` field is set, the number of
choices taken equals to the limit. There is always a valid answer in the chosen choices.

``error_message`` and ``success_message`` are messages that will be displayed on error/success.
They are parsed in RST and are not mandatory.

Multiple choice problem input's are available in the ``run`` script (see :doc:`run_file`)
directly with the id of the problem. The input can be either an array of
integer if ``multiple`` is true or an integer. Choices are numbered sequentially from 0.

