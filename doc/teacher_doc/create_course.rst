.. _course:

Creating a new course
=====================

Courses are defined by subdirectories found in the *tasks directory*, which has been specified in the configuration.
See :ref:`ConfigReference`. These subdirectories are composed of a ``course.yaml`` file describing the course parameters
and other subdirectories corresponding to tasks (See :ref:`task`).

Here is an example of the content of a *tasks folder*::

    tasks/
        course_id_1/
            course.yaml
            task_id_1/
                task.yaml
                run
                ...
            ...
        ...

Ideally, you should only give permissions to a course folder to the course administrator if needed. The webapp task
editor should not require you to give this access. If needed, several methods exist. See :ref:`inginious-synchronize`
for Git repository synchronization.

Tutorial
--------

Creating courses is reserved to the super-administrators (See :ref:`ConfigReference`). Course administrators are then
able to configure the course by themselves.

.. note::

    Demonstration tasks are made available for download `here <https://github.com/UCL-INGI/INGInious-demo-tasks>`_. They
    can also be downloaded and installed automatically via the :ref:`inginious-install` script.

Using the webapp
````````````````

#. As a super-administrator, go to the bottom of the course list and enter a new course id, for instance ``demo``,
   and click on *Create new course*. A newly created hidden  course named *demo* appears on the list.
#. Click on that course, and then on *Course administration* to change the course parameters, add course
   administrators and tasks.

Please note that, if you give access to the course directory to course administrators, you still have to do some
manual work for this to be effective.

Manually
````````

The course description is a YAML file containing all the course parameters used by INGInious.
Here is a simple course description. Put this file with the name ``course.yaml`` in a newly created ``demo`` folder in
your tasks directory.

.. code-block:: yaml

    name: "[DEMO] Demonstration course"
    admins:
    - demouser

This elementary course description file will make a new publicly visible course with id ``demo`` appear as
*[DEMO] Demonstration course* on the course list.

.. _course.yaml:

Course description files
------------------------

Inside the task folder, courses are identified by subdirectories name by their course id and containing a ``course.yaml``
file. For instance, this file, for a course with id ``courseid1``, should be placed in a ``courseid1`` subdirectory.

``course.yaml`` is a YAML file containing the course configuration.

.. code-block:: yaml

    admins:
      - demouser
    name: "[DEMO] Demonstration course"
    tutors: []
    groups_student_choice: false
    use_classrooms: true
    accessible: true
    registration: true
    registration_password: null
    registration_ac: null

While the ``course.yaml`` file must be present at the course root dir, all the fields inside are actually only used by
the webapp. Here are the possible fields to set:

- ``name``
  Displayed name of the course on the course list.

- ``admins``
  List of administrators usernames. These users will have complete administrations right on the course.

- ``tutors``
  List of tutors usernames (restricted-rights teaching assistants). These users will have read-only rights on the
  course content. They cannot change course parameters nor tasks, cannot replay submissions or wipe the course data.
  However, they can manage the classroom composition and download all the student submissions.

- ``accessible``
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

- ``registration``
  When this field is defined, users can only register to the course between the defined period.
  It takes the same arguments as ``accessible``.

- ``allow_unregister``
  If this field is defined and set to ``false``, then students are not allowed to auto-unregister from the course.

- ``registration_password``
  A password that is asked upon registration to the course. If empty or not defined, no password will be asked.

- ``registration_ac``
  Access control (AC) method. Can be ``null`` (anyone can register), ``username`` (filter by username), ``realname``
  (filter by real name) or ``email`` (filter by email address). If AC is activated, the allowed values for the filter
  should be set in the ``registration_ac_list`` key.

- ``registration_ac_list``
  If AC is activated, ``registration_ac_list`` should contain a list of values for the filter.

- ``nofrontend``
  If this field is defined and set to ``true``, then the course won't be displayed on the webapp course list.

- ``groups_student_choice``
  If this field is defined and set to ``true`` and if collaborative work is activated for a given task, students will be
  invited to register by themselves for a group or team before submitting.

- ``use_classrooms``
  If this field is set to ``true``, the classroom model will be used, otherwise, the team model will be used. The default
  value for this field is ``true``. (See :ref:`groups`)
