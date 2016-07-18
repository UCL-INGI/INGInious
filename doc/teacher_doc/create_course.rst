.. _course:

Creating a new course
=====================

A course is defined by a folder under the *tasks folder* (see :ref:`tasks folder`).

.. _task directory: `

To be valid, a course must contain a *course.yaml* file at its root.
The format of that file is defined below.
It can also define several tasks in subfolders.

Here is an example of the content of a *tasks folder*::

    tasks/
        course_name_1/
            course.yaml
            task_1/
                task.yaml
                run
                ...
            task2/
                task.yaml
                run
                ...
        course_name_2/
            course.yaml
            assignment1/
                task.yaml
                run
                ...
            midterm/
                task.yaml
                run
                ...
            final/
                task.yaml
                run
                ...

Most of the time (this is the case in INGI_) the teaching team do not have direct
access to the *tasks* folder, but only to the folder of its courses.

In the main *tasks* folder, each course (for example for the course with id *course_name*)
must have a folder named *course_name*, and, inside this folder, a file called *course.yaml*.


.. _course.yaml:

course.yaml
```````````

*course.yaml* is a YAML file located at the root of a course folder
and containing basic informations about the course.
For exemple, here is what ``course.yaml`` may look like for a criminology course::

    admins:
      - holmes
      - watson
    name: Introduction to criminology

Only username that are in the ``admins`` list are available to see all submissions and statistics.
(a user is always able to see his own submissions)
The ``admins`` is only needed when using the frontend.

There are other fields that are available in the frontend:

.. _accessible_field:

``accessible``
    When this field is defined, the course is only visible if within the defined period.
    A course is always accessible to its admins, and is only hidden to normal users, 
    even if they are registered to the course.
    This field can contain theses values:

    ``true``
        the task is always accessible;
    ``false``
        the task is never accessible;
    ``"<start>/<end>"``
        where <start> and <end> are either empty or valid dates like "2014-05-10 10:11:12" or "2014-06-18".
        The task is only accessible between <start> and <end>.
        If one of the values is empty, the corresponding limit does not apply.

        Dates are always considered as a precise instant (to te lowest resolution of the clock).
        For example, "2014-05-21" is expanded to "2014-05-21 00:00:00".
        This means that start limits are inclusive, while end limits are exclusive.

        Some examples::

            "2014-05-21 / 2014-05-28"
            "/ 2014-01-01 " # (strictly) before january the first
            "2030-01-01 /" # opens in 2030
            "/" # Always open
            "/ 2013-12-31 23:59:59" # closes one minute before "/ 2014-01-01"

``registration``
    When this field is defined, users can only register to the course between the defined period.
    It takes the same arguments as ``accessible``.

``registration_password``
    A password that is asked upon registration to the course. If empty or not defined, no password will be asked.

``registration_ac``
    Access control method. Can be "null" (anyone can register), "username" (filter by username), "realname" (filter by real name) or "email" (filter by email address).
    If AC is activated, the allowed values for the filter should be set in the ``registration_ac_list`` key.

``registration_ac_list``
    If AC is activated, ``registration_ac_list`` should contain a list of values for the filter.

``nofrontend``
    If this field is defined and set to ``true``, then the course won't be displayed on the frontend, but will still be available for the plugins.

``groups_student_choice``
    If this field is defined and set to ``true`` and if collaborative work is activated for a given task, students will be
    invited to register for a group before submitting.

``use_classrooms``
    If this field is set to ``true``, the classroom model will be used, otherwise, the team model will be used. The default
    value for this field is ``true``

.. _INGI: http://www.uclouvain.be/ingi.html
