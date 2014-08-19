INGInious
=========

<img align="right" src="static/images/logo.png">

INGInious is an intelligent grader that allows secured and automated testing of code made by students.

It is written in Python and uses [Docker](https://www.docker.com/) to run student's code inside a secured environment.

INGInious provides a backend which manages interaction with Docker and grade code, and a frontend which allows students to submit their code in a simple and beautiful interface. The frontend also includes a simple administration interface that allows teachers to check the progression of their students and to modify exercices in a simple way.

The backend is independent of the frontend and was made to be used as a library.

INGInious can be used as an external grader for EDX. The course [Paradigms of Computer Programming - Fundamentals](https://www.edx.org/course/louvainx/louvainx-louv1-1x-paradigms-computer-2751) 
uses INGInious to correct students' code.

Documentation
-------------

On Linux, run `make html` in the directory `/doc` to create a html version of the documentation.


Notes on security
-----------------

Docker containers can be used securely with SELinux enabled. Please do not run untrusted code without activating SELinux.
