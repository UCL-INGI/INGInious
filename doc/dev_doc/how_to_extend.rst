How to extend INGInious
=======================

Creating a new frontend
-----------------------

INGInious is mainly a backend that is agnostic. It can be used to run nearly everything.
The backend's code is in :doc:`backend`. You must use these classes to run new jobs.

The :doc:`common` contains classes that are intended to be inherited by new "frontends".
The frontend given with INGInious is in fact an (big) extension of the :doc:`common` module.
You can use it as an example on how to extend INGInious.
