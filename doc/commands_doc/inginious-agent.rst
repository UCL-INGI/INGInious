inginious-agent
===============

Start an agent. This command is usually used only by users who know what they are doing.

.. program:: inginious-agent

::

    inginious-agent [-h] [--dir DIR] [--tasks TASKS] port

.. option:: -h, --help

   Display the help message.

.. option:: --dir DIR

   Path to a directory where the agent can store information,
   such as caches. Defaults to ./agent_data

.. option:: --task TASKS

   The path to the directory **containing the courses**. Default to ``./tasks``.

.. option:: port

   Port to listen to

