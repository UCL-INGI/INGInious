backend package
===============

Job workflow
------------

When a job is submitted to an object of the class JobManager, the following process happens:

#. 	The job is processed internally and problems that does not involve a docker container are processed.

#.	If the job need to be launched in a container:

	#.	An :doc:`agent` is selected. Currently, it is done using a round-robin, but it should evolve soon.

    #.  The job is sent to the agent

    #.  The agent starts a *grading container*, that can start itself zero, one or more *student containers*, at will;

    #.  Once the *grading container* is done, the agent get back the grading information...

    #.  ... and send it to the backend.

    #.  The backend then merge the results of local (multiple-choice questions, ...) and remote grading

#.  The result is given back to the caller via a callback function.

backend.job_managers.abstract module
------------------------------------

.. automodule:: backend.job_managers.abstract
    :members:
    :undoc-members:
    :show-inheritance:

backend.job_managers.local module
---------------------------------

.. automodule:: backend.job_managers.local
    :members:
    :undoc-members:
    :show-inheritance:

backend.job_managers.remote_docker module
-----------------------------------------

.. automodule:: backend.job_managers.remote_docker
    :members:
    :undoc-members:
    :show-inheritance:

backend.job_managers.remote_manual_agent module
-----------------------------------------------

.. automodule:: backend.job_managers.remote_manual_agent
    :members:
    :undoc-members:
    :show-inheritance:

backend.hook_manager module
---------------------------

.. automodule:: backend.hook_manager
    :members:
    :undoc-members:
    :show-inheritance:

Utilities to handle job managers
--------------------------------

backend.helpers.job_manager_sync module
```````````````````````````````````````

.. automodule:: backend.helpers.job_manager_sync
    :members:
    :undoc-members:
    :show-inheritance:

backend.helpers.job_manager_buffer module
`````````````````````````````````````````

.. automodule:: backend.helpers.job_manager_buffer
    :members:
    :undoc-members:
    :show-inheritance:
