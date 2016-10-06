INGInious
=========

.. image:: http://jenkins2.info.ucl.ac.be/job/INGInious/badge/icon
    :target: http://jenkins2.info.ucl.ac.be/job/INGInious/
.. image:: https://landscape.io/github/UCL-INGI/INGInious/master/landscape.svg?style=flat
    :target: https://landscape.io/github/UCL-INGI/INGInious/master
.. image:: https://readthedocs.org/projects/inginious/badge/?version=latest
    :target: https://readthedocs.org/projects/inginious/?badge=latest
.. image:: https://badges.gitter.im/Join%20Chat.svg
    :target: https://gitter.im/UCL-INGI/INGInious?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge


INGInious is an intelligent grader that allows secured and automated testing of code made by students.

It is written in Python and uses Docker_ to run student's code inside a secured environment.

INGInious provides a backend which manages interaction with Docker and grade code, and a frontend which allows students to submit their code in a simple and beautiful interface. The frontend also includes a simple administration interface that allows teachers to check the progression of their students and to modify exercices in a simple way.

The backend is independent of the frontend and was made to be used as a library.

INGInious can be used as an external grader for EDX. The course `Paradigms of Computer Programming - Fundamentals`_ uses INGInious to correct students' code.

.. _Docker: https://www.docker.com/
.. _Paradigms of Computer Programming - Fundamentals: https://www.edx.org/course/louvainx/louvainx-louv1-1x-paradigms-computer-2751

Documentation
-------------

The documentation is available on Read the Docs: http://inginious.readthedocs.org/en/latest/index.html

On Linux, run ``make html`` in the directory ``/doc`` to create a html version of the documentation.


Notes on security
-----------------

Docker containers can be used securely with SELinux enabled. Please do not run untrusted code without activating SELinux.

Mailing list
------------

A mailing list for both usage and development discussion can be joined by registering here_.

..  _here: https://sympa-2.sipr.ucl.ac.be/sympa/info/inginious
