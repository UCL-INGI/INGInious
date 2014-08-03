INGInious
=========

INGInious is an intelligent grader that allows secured and automated testing of code made by students.

It is written in Python and uses [Docker](https://www.docker.com/) to run student's code inside a secured environment.

INGInious provides a backend which manages interaction with Docker and grade code, and a frontend which allows students to submit their code in a simple and beautiful interface.

The backend is independent of the frontend and was made to be used as a library.

Documentation
-------------

On Linux, run `make html` in the directory `/doc` to create a html version of the documentation.


Notes on security
-----------------

Docker containers can be used securely with SELinux enabled. Please do not run untrusted code without activating SELinux.
