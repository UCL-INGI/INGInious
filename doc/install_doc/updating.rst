Updating INGInious
==================

Updating the sources
--------------------

To fetch the latest updates on the Git repository master branch :
::

   $ pip3 install --upgrade git+https://github.com/UCL-INGI/INGInious.git
If you installed INGInious via Pipy, you can simply upgrade it using:
::

   $ pip3 install --upgrade inginious

Updating your containers
------------------------

The provided containers can be automatically updated using:
::

    $ inginious-container-update

For your own or third-party containers, please refer to :ref:`new_container`.

Updating the configuration
--------------------------

Most of the time, you won't need to update your configuration. If something goes wrong, backup your existing
configuration file(s) and run ``inginious-install`` again. For further details, please refer to :ref:`inginious-install`
or :ref:`ConfigReference`.
