inginious-remote-debug
======================

Allow to connect to remote SSH server running on containers, throught an agent or the web app.

.. program:: inginious-webapp

::

    inginious-webapp HOST

.. option:: HOST

   Remote host. Generally the agent or the web app, with a specific port. ``HOST`` must be in the form ``hostname.or.ip:port``.

The command then takes as input a connection id and a private key, given by the agent or the web app.