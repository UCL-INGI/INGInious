.. _course.yaml:

Course description files
------------------------

The course description is a YAML file named ``course.yaml`` containing all the course parameters used by INGInious.
Here is a simple course description.

.. code-block:: yaml

    name: "[DEMO] Demonstration course"
    admins:
    - demouser

This elementary course description file will make a new publicly visible course appear as
*[DEMO] Demonstration course* on the course list.

Inside the task folder, courses are identified by subdirectories name by their course id and containing a ``course.yaml``
file. For instance, this file, for a course with id ``courseid1``, should be placed in a ``courseid1`` subdirectory.

``course.yaml`` is a YAML file containing the course configuration.

.. code-block:: yaml

    admins:
      - demouser
    name: "[DEMO] Demonstration course"
    tutors: []
    groups_student_choice: false
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
  However, they can manage the audience composition and download all the student submissions.

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
  Access control (AC) method. Can be ``null`` (anyone can register), ``username`` (filter by username), ``binding``
  (filter by binding auth method) or ``email`` (filter by email address). If AC is activated, the allowed values for the filter
  should be set in the ``registration_ac_list`` key.

- ``registration_ac_list``
  If AC is activated, ``registration_ac_list`` should contain a list of values for the filter.
  ``*`` acts as a wildcard.

- ``nofrontend``
  If this field is defined and set to ``true``, then the course won't be displayed on the webapp course list.

- ``groups_student_choice``
  If this field is defined and set to ``true`` and if collaborative work is activated for a given task, students will be
  invited to register by themselves for a group before submitting.