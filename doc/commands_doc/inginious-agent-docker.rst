.. _inginious-agent-docker:

inginious-agent-docker
======================

Start a Docker grading agent. This is typically only used when running the INGInious backend remotely. If you configured
INGInious to use a local backend, it is automatically run by ``inginious-webapp`` or ``inginious-lti``.

.. program:: inginious-agent-docker

::

    inginious-agent-docker [-h] [--debug-host DEBUG_HOST]
                           [--debug-ports DEBUG_PORTS] [--tmpdir TMPDIR]
                           [--tasks TASKS] [--concurrency CONCURRENCY] [-v]
                           backend

.. option:: -h, --help

   Display the help message.

.. option:: --debug-host DEBUG_HOST

   The agent hostname for SSH debug. If not specified, the agent autodiscover the public IP address.

.. option:: --debug-ports DEBUG_PORTS

   Range of port for job remote debugging. By default it is 64120-64130

.. option:: --tmpdir TMPDIR

   Path to a directory where the agent can store information,
   such as caches. Defaults to ./agent_data

.. option:: --tasks TASKS

   The path to the directory **containing the courses**. Default to ``./tasks``.

.. option:: --concurrency CONCURRENCY

    Maximal number of jobs that can run concurrently on this agent. By default, it is the two times the number
    of cores available.

.. option:: -v, --verbose

   Increase output verbosity: logging level to DEBUG.

.. option:: backend

   The backend port, using the following syntax : ``protocol://host:port``. E.g. ``tcp://127.0.0.1:2001``.
   The agent will connect to the backend listening on that port.
