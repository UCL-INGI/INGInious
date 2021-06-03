Understand INGInious
====================

INGInious is made from several different packages:

- The common which contains basic blocks, like *tasks*.
  Derivates from this blocks are created by the frontend and other modules.
  The common package does not need the :ref:`backend` nor the :ref:`frontend`;
- The :ref:`agent`, that runs jobs. It interacts directly with Docker to start new containers, and sends the grades back to the backend.
  A specific part of the :ref:`backend` is in charge of starting the agents automatically; you most of time won't need to it manually.
  The agent needs to be run *on* the Docker host, as it interacts with other containers with Unix sockets, and must also interact with CGroups
  to allow a very fine management of timeouts and memory limits.
- The :ref:`backend`, which is in charge of handling grading requests, giving the work to distant agents;
  the backend is made to be simple and frontend-agnostic; you can 'easily' replace the frontend by something else.
  The backend only store information about *running* tasks. This point is important when considering replication and horizontal scalability (see
  later)
- The :ref:`frontend` which is a web interface for the backend. It provides a simple yet powerful interface for students and teachers.
  It is made to be "stateless": all its state is stored in DB, allowing to replicate the frontend horizontally.
- The client which is an abstract layout for other clients than the frontend. It provides classes and methods that handle jobs.
  This simplify the connection between INGInious and external frontends.

Basic architecture of INGInious
-------------------------------
The following schema shows the basic architecture of INGInious:

.. image:: /dev_doc/internals_doc/inginious_arch.png
    :align: center

Scalability of Docker hosts
---------------------------
In order to share the work between multiple servers, INGInious can use multiple agents, as shown in the following schema.
The completely horizontal scalability is (nearly) without additional configuration, and can be made fully automatic with a bit of work.

.. image:: /dev_doc/internals_doc/inginious_arch_docker.png
    :align: center

Scalability of the INGInious frontend
-------------------------------------
As the backend only stores information about *running* submission, and the frontend is stateless,
we can use the replication feature of MongoDB to scale horizontally the frontends too.
The (final) schema below shows the most advanced way of configuring INGInious,
with multiple frontends replicated and multiple Docker hosts.

.. image:: /dev_doc/internals_doc/inginious_arch_full.png
    :align: center

Grading containers and student containers
-----------------------------------------

A *grading container* is a container that do the grading. It typically runs a script made by a teacher or its assistants, a launch sub-containers,
called *student containers*, that will separately jail code made by students.

A single *grading container* can launch more than one *student container*; the interaction between the two is completely secured by the agent.

Jobs
----

When you send a student's input to the backend, it creates what we call a *job*.
Jobs are sent to an object called the *Client*, which itself is a simple communication layer to a job queue that we call the *Backend*.
The *Backend* itself can be used by multiple *Clients*, and dispatch jobs among *Agents*, which can be of different types (for now, we have two
kinds of agents, *DockerAgent* and *MCQAgent*)

When a job is submitted, a callback must be given: it is automatically called when the task is done, asynchronously.

Submission
----------

A submission is an extension of the concept of job. A submission only exists in the
frontend, and it is mainly a job saved to db.
