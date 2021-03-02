.. _course:

Courses
=======

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


.. toctree::
   :maxdepth: 2

   course_tuto
   course_description
   course_admin