What is INGInious?
==================

Made by the INGI_ department at the Catholic University of Louvain,
INGInious is a tool built in Python_ on the top of Docker_, that allows teacher to 
automatize the test on the code made by the students.

INGInious is completely language-agnostic: you can make containers_ for every language that
you can run on a Linux distribution.

.. _Python: http://www.python.org/
.. _Docker: https://www.docker.com/
.. _INGI: http://www.uclouvain.be/ingi.html

How does INGInious work?
------------------------

INGInious is basically a backend (which is, in Python, the :doc:`../dev_doc/backend`) which receives
the code of the student and send it to a Docker container_. The Docker container then makes
some verifications on the code of the student and returns a status, that can be *success*,
*crash*, *timeout*, or *failed*.

INGInious also provides a frontend (you guessed it, this is the :doc:`../dev_doc/frontend` in Python).
Made with MongoDB as database, the frontend is in fact an extension of the backend,
and allows students to work directly on a website. Statistics are available for the teachers through a dedicated interface.

.. _container:
.. _containers:

Docker containers
`````````````````

Docker containers are small virtual operating systems that provides isolation_ between the
processes and resources of the host operating system.
Docker allow to create and ship any software on any free Linux distribution.

As there are no hypervisor, the processes launched in the container are in fact directly
run by the host operating system, which allows applications to be amazingly fast.

Docker allow teachers to build new containers easily, to add new dependencies to the tests
applied on the student's code.

.. _isolation:

Isolation
`````````

Isolation allows teachers and system administrators to stop worrying about the code that
the students provides. 

For example, if a student provides a forkbomb instead of a good code for the 
test, the forkbomb will be contained inside the container. The host operating system
(the computer that runs INGInious) won't be affected.

The same thing occurs with memory consumption and disk flood. The running time of a code
is also limited.

Compatibility
-------------

INGInious provides two compatibly layers with the non-longer-maintained Pythia Project.
Tools to convert old Pythia tasks to INGInious tasks are available in the folder
`dev_tools`.

The converted tasks are then 100% compatible with INGInious.