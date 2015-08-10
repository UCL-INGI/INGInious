inginious-lti
=============

Starts the LTI Frontend. This command can run a standalone web server (see ``--host`` and ``--port`` options),
but also as a FastCGI backend.

.. program:: inginious-lti

::

    inginious-lti [-h] [--config CONFIG] [--host HOST] [--port PORT]

.. option:: --config

   Specify the configuration file to use. By default, it is configuration.lti.yaml.

.. option:: --host HOST

   Specify the host to which to bind to. By default, it is localhost.

.. option:: --port PORT

   Specify the port to which to bind to. By default, it is 8080.

.. option:: -h, --help

   Display the help message.