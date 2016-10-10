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

This obviously defines two LTI keys, ``consumer_key_1`` and ``consumer_key_2``, with passwords ``a_very_secret_password`` and
``wow_such_secret``.

Setting up your LMS
-------------------

Setting up edX
``````````````

edX provides `a good tutorial on how to install LTI components`_.

When it asks for the ``LTI passport``, you have to enter it in the format ``an_id_that_you_define:consumer_key:password``.
A good example, taking values from the start of this document, would be

::

    inginious:consumer_key_1:a_very_secret_password

The ``launch url`` is, if your server is located at ``https://HOST:PORT/``, and you want to load the task ``task_id`` from the course ``course_id``:

::

    https://HOST:PORT/launch/course_id/task_id

Please note that for now, edX *needs* https. This means you will probably have to buy a certificate.

.. _a good tutorial on how to install LTI components: http://edx-partner-course-staff.readthedocs.org/en/latest/exercises_tools/lti_component.html

Setting up Moodle
`````````````````

Under edition mode, select ``add an activity``, choose ``external tool``, and confirm.

Directly click on ``Show more...``. Fill in the activity name.

The ``Launch URL`` is, if your server is located at ``https://HOST:PORT/``, and you want to load the task ``task_id`` from the course ``course_id``:

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
You are on your own for the configuration, though; but with the LTI keys and the launch URL, it should be enough to configure anything.

Troubleshooting Problems
````````````````````
Some things to check if you're having problems:

* INGInious uses PyLTI which uses oauth, oauth2 and libhttp2. The list of 
  certificate authorities known to libhttp2 may be out of day with your
  host operating system. In particular, as of August 2016, it does not
  include the LetsEncrypt CA, and thus websites protected with a LetsEncrypt
  certificate won't work (you won't be able to push grades back)

* LTI uses OAuth which uses time-based replay prevention. You need to insure
  that your webserver (LTI consumer) and LTI producer have reasonably
  synchronous clocks.

* You may find `http://ltiapps.net/test/tp.php` and `http://ltiapps.net/test/t.php`
  useful when debugging producers and consumers.

