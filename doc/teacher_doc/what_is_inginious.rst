What is INGInious?
==================

INGInious provides a simple and secure way to execute and test untrusted code.
It has been developed by the INGI_ department (UCL_) to grade programming assignments.
The whole tool is written in Python_ (version 2).
Behind the scenes, it relies on Docker_ to provide secure execution environments and on MongoDB_ to keep track of submissions.

INGInious is completely language-agnostic: if you can execute some code on a Linux machine, INGInious will be able to run it.
A container shipping Wine_ could even grade a '.exe'!

INGInious also provides tools to work directly with edX, and will be soon compatible with more MOOC platforms.

As of July 2015, it is used both directly by the teaching staff of INGI_ for more than ten courses, and is used by two MOOCs, Louv1.1x_
and Louv1.2x_.

.. _Python: http://www.python.org
.. _Docker: https://www.docker.com
.. _INGI: http://www.uclouvain.be/ingi.html
.. _UCL: http://www.uclouvain.be
.. _MongoDB: http://www.mongodb.com
.. _Wine: http://www.winehq.org
.. _edX: https://www.edx.org
.. _Louv1.1x: https://www.edx.org/course/louvainx/louvainx-louv1-1x-paradigms-computer-2751
.. _Louv1.2x: https://www.edx.org/course/louvainx/louvainx-louv1-2x-paradigms-computer-4436


How does INGInious work?
------------------------

INGInious is based on the concept of tasks (see :ref:`task`). A task is a set of one or more related (sub)questions.
For each task, an infinite number of submissions is allowed, but a user must wait for the result of its current submission before trying a new one.

For simplicity, tasks are grouped by courses (see :ref:`course`).
Usually, an INGInious course has one task per assignment.

A submission is a set of deliverables (chunks of code, files, archives, etc.) that correspond each to one of the (sub)questions of the task.
These files are made available to the *run file* (see :ref:`run file`), a special script provided by the task.
That script is responsible for providing feedback on the submission by compiling, executing or applying any form of checking and testing to the deliverables.
In its simplest form, the feedback consists of either *success* or *failed*.

This *run file* is run inside a container (precisely, a *grading container*), that completely jails the execution of the script, because even teachers
and assistants are never fully trusted. *Grading containers* are able to start sub-containers, called *student containers*, that runs the scripts
that the students sent with their submission, in another jailed environment.

This separation in two step of the grading is mandatory to ensure a complete security for the server hosting INGInious *and* a complete security of
the grading process, making impossible for the student to interact "badly" with the *run script*.

These containers are created/described by very simple files called Dockerfile. They allow to create containers for anything that runs on Linux.
For details about to create new containers and add new languages to INGInious, see :doc:`create_container`.

Architecture
````````````

INGInious comes with three distinct parts, the backend (and its agent) and a frontend.

The backend (see :doc:`../dev_doc/backend`) receives the code of the students and sends it to its agent (see :doc:`../dev_doc/agent`), which is then
responsible to send it to a Docker container_, and interact with the request made by the container.

That container then makes some verifications on the submission and returns one of the following four possible status : *success*, *crash*, *timeout*,
or *failed*.

INGInious also provides a frontend (see :doc:`../dev_doc/frontend`).
Made with MongoDB as database, the frontend is in fact an extension of the backend and allows students to work directly on a website.
This frontend also provides statistics and management tools for the teachers.

Most of these functionalities can be extended through plugins.

For a more advanced view of the architecture of INGInious, see :doc:`../dev_doc/understand_inginious`.

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
applied on the student's code (see :doc:`create_container`)

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
