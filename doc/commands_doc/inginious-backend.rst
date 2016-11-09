.. _inginious-backend:

inginious-backend
=================

Start an INGInious backend. This is typically only used when running the INGInious backend remotely. If you configured
INGInious to use a local backend, it is automatically run by ``inginious-webapp`` or ``inginious-lti``.

.. program:: inginious-backend

::

    inginious-backend [-h] [-v] agent client

.. option:: -h, --help

   Display the help message.

.. option:: -v, --verbose

   Increase output verbosity: logging level to DEBUG.

.. option:: agent

    The agents port, using the following syntax : ``protocol://host:port``. E.g. ``tcp://127.0.0.1:2001``.
    The backend will listen for grading agents on that port.

.. option:: client

    The clients port, using the following syntax : ``protocol://host:port``. E.g. ``tcp://127.0.0.1:2000``.
    The backend will listen for client frontend on that port.
