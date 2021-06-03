What is INGInious?
==================

INGInious provides a simple and secure way to execute and test untrusted code.
It has been developed by the INGI_ department (`Université catholique de Louvain`_) to automatic grading of programming
assignments. The whole tool is written in Python_ (version 3.5+) and relies on Docker_ to provide secure execution
environments and on MongoDB_ to keep track of submissions.

INGInious is completely language-agnostic and is able to run anything. Currently, this is limited to Linux programs as only
Linux containers are provided and supported.

INGInious also provides an LTI_ module, allowing its integration to your existing (Open) edX_, Moodle_,... courses.

.. _LTI: http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html
.. _Python: http://www.python.org
.. _Docker: https://www.docker.com
.. _INGI: http://www.uclouvain.be/ingi.html
.. _`Université catholique de Louvain`: http://www.uclouvain.be
.. _MongoDB: http://www.mongodb.com
.. _Moodle: http://moodle.org
.. _edX: https://www.edx.org

How does INGInious work?
------------------------

INGInious is based on the concept of tasks (see :ref:`task`). A task is a set of one or more related (sub)questions.
For each task, an infinite number of submissions is allowed, but a user must wait for the result of its current submission before trying a new one.

For simplicity, tasks are grouped by courses (see :ref:`course`).
Usually, an INGInious course has one task per assignment.

A submission is a set of deliverables (chunks of code, files, archives, etc.) that correspond each to one of the (sub)questions of the task.
These files are made available to the *run file* (see :ref:`run_file`), a special script provided by the task.
That script is responsible for providing feedback on the submission by compiling, executing or applying any form of checking and testing to the deliverables.
In its simplest form, the feedback consists of either *success* or *failed*.

This *run file* is run inside a container (precisely, a *grading container*), that completely jails the execution of the script, because even teachers
and assistants are never fully trusted. *Grading containers* are able to start sub-containers, called *student containers*, that runs the scripts
that the students sent with their submission, in another jailed environment.

This separation in two step of the grading is mandatory to ensure a complete security for the server hosting INGInious *and* a complete security of
the grading process, making impossible for the student to interact "badly" with the *run script*.

These containers are created/described by very simple files called Dockerfile. They allow to create containers for anything that runs on Linux.
For details about to create new containers and add new languages to INGInious, see :doc:`teacher_doc/create_container`.

Architecture
````````````

INGInious comes with three distinct parts, the backend (and its agent) and a frontend.

The backend (see :ref:`backend`) receives the code of the students and sends it to its agent (see :ref:`agent`), which is then
responsible to send it to a Docker container_, and interact with the request made by the container.

That container then makes some verifications on the submission and returns one of the following four possible status : *success*, *crash*, *timeout*,
or *failed*.

INGInious also provides a frontend (see :ref:`frontend`).
Made with MongoDB as database, the frontend is in fact an extension of the backend and allows students to work directly on a website.
This frontend also provides statistics and management tools for the teachers.

Most of these functionalities can be extended through plugins.

For a more advanced view of the architecture of INGInious, see :doc:`dev_doc/internals_doc/understand_inginious`.

.. _container:
.. _containers:

Docker containers
`````````````````

Docker containers are small virtual operating systems that provides isolation_ between the
processes and resources of the host operating system.
Docker allow to create and ship any software on any free Linux distribution.

As there are no hypervisor, the processes launched in the container are in fact directly
run by the host operating system, which allows applications to be amazingly fast.

Docker allows teachers to build new containers easily, to add new dependencies to the tests
applied on the student's code (see :doc:`teacher_doc/create_container`)

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

INGInious provides two compatibility layers with Pythia v0 and v1. Except the task description file which has to be
updated, everything is 100% compatible with INGInious.
