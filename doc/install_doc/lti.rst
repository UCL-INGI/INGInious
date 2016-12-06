.. _configure_LTI:

Configuring the LTI frontend
============================

In order to use the LTI frontend with your favorite LMS, you first have to define your LTI keys (consumer key and secret), then installing them on
your LMS.

Defining your LTI keys
----------------------

The LTI keys are defined in the configuration file of the LTI frontend, usually ``configuration.lti.yaml``.
Here is an example of configuration:

::

    lti:
        consumer_key_1:
            secret: a_very_secret_password
        consumer_key_2:
            secret: wow_such_secret
            courses:
                - my_course

This obviously defines two LTI keys, ``consumer_key_1`` and ``consumer_key_2``, with passwords ``a_very_secret_password`` and
``wow_such_secret``.

By default, consumer keys allow accessing all courses data from the consumer. If you want a consumer to be restricted to
only one course data, use the ``courses`` field and specify the list of courses to give access to. This is illustrated in
the example with ``consumer_key_2``.

Setting up your LMS
-------------------

Setting up (Open) edX
`````````````````````

edX provides `a good tutorial on how to install LTI components`_.

When it asks for the ``LTI passport``, you have to enter it in the format ``an_id_that_you_define:consumer_key:password``.
A good example, taking values from the start of this document, would be

::

    inginious:consumer_key_1:a_very_secret_password

The ``launch url`` is, if your server is located at ``https://HOST:PORT/``, and you want to load the task ``task_id`` from the course ``course_id``:

::

    https://HOST:PORT/launch/course_id/task_id

Please note that, for now, official edX *needs* https. You also need to set the LTI activity to accept a score back from INGInious, without which the activity won't launch.

.. _a good tutorial on how to install LTI components: http://edx-partner-course-staff.readthedocs.org/en/latest/exercises_tools/lti_component.html

Setting up Moodle
`````````````````

Under edition mode, select ``add an activity``, choose ``external tool``, and confirm.

Directly click on ``Show more...``. Fill in the activity name.

The ``Launch URL`` is, if your server is located at ``https://HOST:PORT/``, and you want to load the task ``task_id``
from the course ``course_id``:

::

    https://HOST:PORT/launch/course_id/task_id

For the field ``Launch Container``, the best value is "Embded without block".
``Consumer key`` and ``Consumer secret`` are the LTI key you defined earlier.
In the ``Privacy`` fieldset, verify that ``accept grades from the tool`` is checked.
Leave the other fields blank (or modify them as you want).

Save, and it should work.

Setting up other LMS
````````````````````

INGInious has only been tested with edX and Moodle, but it should work out-of-the-box with any LMS that respects LTI 1.1.
You are on your own for the configuration, though; but with the LTI keys and the launch URL, it should be
enough to configure anything.
