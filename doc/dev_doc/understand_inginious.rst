Understand INGInious
====================

INGInious is made from three different packages:

- The :doc:`common` which contains basic blocks, like *tasks* and 
  *courses*. Derivates from this blocks are created by the frontend and other modules.
  The :doc:`common` does not need the :doc:`backend` nor the :doc:`frontend`.
- The :doc:`backend` which contains only the needed classes to allow running tasks.
- The :doc:`frontend` which is a web interface for the backend. 

Jobs
----

When you send a student's input to the backend, it creates what we call a *job*.
Jobs are sent to an object called the *Job Manager*, which handles the run of the task

More information about the way a *Job Manager* handles tasks is available in the documentation of the JobManager class.

When a job is submitted, a callback must be given: it is automatically called when the task is done, asynchronously.

Submission
----------

A submission is an extension of the concept of job. A submission only exists in the
frontend, and it is mainly a job saved to db.