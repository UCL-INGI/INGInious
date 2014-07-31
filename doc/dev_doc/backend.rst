backend package
===============

Job workflow
------------

When a job is submitted to an object of the class JobManager, the following process happens:

#. 	The job is processed internally and problems that does not involve a docker container are processed.

#.	If the job need to be launched in a container:

	#.	A new docker instance is selected. The docker instance with the less running jobs is chosen.
	
	#.	The job is then sent to a process pool, which runs the *submitter* function.
		The submitter function is in charge of connecting to the chosen docker instance and to run a new container instance.
		It then put the container id of the newly created container in the wait queue of the chosen docker instance.
	
	#.	The queue is read by processes called *waiters*. One or more *waiter* is associated with each docker instance. A *waiter*
		is in charge of emptying the wait queue and to periodically verify that a container has ended.
		When a container has done its work, the *waiter* get the results from the docker instance, and push it in the callback queue (internally called the *done queue*)
	
	Else
	
	#.	The job is put in the callback queue
	
#.	The callback queue is then read by threads (which are run inside the JobManager's process) called *callback managers*. 
	They are in charge of calling the callbacks functions given when submitting the job.
	It is important that callback are made inside the JobManager's process. This allow users of the JobManager object to use non-pickable callback functions, such as bound functions.
	(this allows to be more flexible).
	
#.	If the job was launched in a container, the callback manager also start the function *deleter* in the process pool, which deletes the container.
	
Submodules
----------

backend.job_manager module
---------------------------------

.. automodule:: backend.job_manager
    :members:
    :undoc-members:
    :show-inheritance:

backend.job_manager_sync module
---------------------------------

.. automodule:: backend.job_manager_sync
    :members:
    :undoc-members:
    :show-inheritance:
    
backend.job_manager_buffer module
---------------------------------

.. automodule:: backend.job_manager_buffer
    :members:
    :undoc-members:
    :show-inheritance:
    
Utilities for the class JobManager
----------------------------------

backend._submitter module
`````````````````````````

.. automodule:: backend._submitter
    :members:
    :undoc-members:
    :show-inheritance:

backend._waiter module
``````````````````````

.. automodule:: backend._waiter
    :members:
    :undoc-members:
    :show-inheritance:

backend._callback_manager module
````````````````````````````````

.. automodule:: backend._callback_manager
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: backend
    :members:
    :undoc-members:
    :show-inheritance:
