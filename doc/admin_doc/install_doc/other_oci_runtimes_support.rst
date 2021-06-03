Support for other OCI runtimes (alpha)
======================================

Docker supports running other Open Container Initiative (OCI) compatible runtimes, such as Kata_.

.. _Kata: https://katacontainers.io/

Some of these runtimes have vastly different methods of running containers compared to the default runtime used by docker (runc).

For example, Kata_ spins virtual machines rather than containers based on cgroups. This allows to (more) safely run container as root.

There is **preliminary**, *alpha* support of using other OCI runtimes in INGInious. By default, INGInious attempts to detect if
runc, crun and kata are available or not. You can use other runtimes by using the ``-runtime`` arg of the ``inginious-agent-docker`` command.

Current limitations
-------------------

For now, the ``run_student`` API/command does not work on runtimes on which
the containers have each different kernels (i.e. are VMs). See below for more information.

Behavior
--------

Runtimes are classified by INGInious in categories:

- Runtimes on which all containers share the same kernel
- Runtimes on which it is safe to run as root

They are not mutually exclusive in theory, but are in practice.

Runtimes on which all containers share the same kernel
''''''''''''''''''''''''''''''''''''''''''''''''''''''

The containers running on these runtimes can use ``run_student``. ``run_student`` currently transfer file descriptor
via unix sockets between containers (for simplicity and performance), and this is not possible between kernels.

Using ``run_student`` on containers running in runtimes that do not share kernel will lead to an error.

Runtimes on which it is safe to run as root
'''''''''''''''''''''''''''''''''''''''''''

On these runtimes, the run file will be run by the user ``root`` (id 0, gid 0) rather than by ``worker`` (id 4242, gid 4242), allowing
to do things normally unsupported such as editing the network stack, mounting things, ...

Installing other runtimes
-------------------------

Please see the documentation of the runtimes to install them in Docker; verify that they work using the ``docker`` CLI.

Then, use the ``--runtime`` of the ``inginious-agent-docker`` command if they are not automatically detected by INGInious (after a restart).