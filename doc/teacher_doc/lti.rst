.. _configure_LTI:

Using through LTI (edX, Moodle, ...)
=====================================

INGInious implements the LTI specification in order to integrate into edX, Moodle, or any other LMS that also implements
this specification. To get started, all you need is to activate the LTI mode in the course administration and define
your LTI keys (consumer key and secret). You'll then be able to use INGInious tasks as activities in your LMS.

Defining LTI keys
-----------------

The LTI keys are defined in the course administration by first activating the LTI mode. Then, add consumer keys and secrets
separated by a colon in the LTI keys field. For instance, here's an example of a set of keys and secrets:

::

        consumer_key_1:a_very_secret_password
        consumer_key_2:wow_such_secret

This obviously defines two LTI keys, ``consumer_key_1`` and ``consumer_key_2``, with passwords ``a_very_secret_password`` and
``wow_such_secret``. You also need to check the *Send grades back* option to actually send the scores from INGInious to your LTI.


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

    https://HOST:PORT/lti/course_id/task_id

Please note that, for now, official edX *needs* https. You also need to set the LTI activity to accept a score back from INGInious if
your have set up INGInious such that scores are sent back.

.. _a good tutorial on how to install LTI components: http://edx-partner-course-staff.readthedocs.org/en/latest/exercises_tools/lti_component.html

Setting up Moodle
`````````````````

Under edition mode, select ``add an activity``, choose ``external tool``, and confirm.

Directly click on ``Show more...``. Fill in the activity name.

The ``Launch URL`` is, if your server is located at ``https://HOST:PORT/``, and you want to load the task ``task_id``
from the course ``course_id``:

::

    https://HOST:PORT/lti/course_id/task_id

For the field ``Launch Container``, the best value is "Embded without block".
``Consumer key`` and ``Consumer secret`` are the LTI key you defined earlier.
In the ``Privacy`` fieldset, check that ``accept grades from the tool`` is checked.
Leave the other fields blank (or modify them as you want).

Save, and it should work.

Setting up other LMS
````````````````````

INGInious has only been tested with edX and Moodle, but it should work out-of-the-box with any LMS that respects LTI 1.1.
You are on your own for the configuration, though; but with the LTI keys and the launch URL, it should be
enough to configure anything.
