INGInious
=========

[![Build Status](https://travis-ci.org/UCL-INGI/INGInious.svg?branch=master)](https://travis-ci.org/UCL-INGI/INGInious)
[![Code Health](https://landscape.io/github/UCL-INGI/INGInious/master/landscape.svg?style=flat)](https://landscape.io/github/UCL-INGI/INGInious/master)
[![Documentation Status](https://readthedocs.org/projects/inginious/badge/?version=latest)](https://readthedocs.org/projects/inginious/?badge=latest)
[![Join the chat at https://gitter.im/UCL-INGI/INGInious](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/UCL-INGI/INGInious?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

<img align="right" src="frontend/common/static/images/logo.png" alt="logo">

INGInious is an intelligent grader that allows secured and automated testing of code made by students.

It is written in Python and uses [Docker](https://www.docker.com/) to run student's code inside a secured environment.

INGInious provides a backend which manages interaction with Docker and grade code, and a frontend which allows students to submit their code in a simple and beautiful interface. The frontend also includes a simple administration interface that allows teachers to check the progression of their students and to modify exercices in a simple way.

The backend is independent of the frontend and was made to be used as a library.

INGInious can be used as an external grader for EDX. The course [Paradigms of Computer Programming - Fundamentals](https://www.edx.org/course/louvainx/louvainx-louv1-1x-paradigms-computer-2751) 
uses INGInious to correct students' code.

Documentation
-------------

The documentation is available on Read the Docs: http://inginious.readthedocs.org/en/latest/index.html

On Linux, run `make html` in the directory `/doc` to create a html version of the documentation.


Notes on security
-----------------

Docker containers can be used securely with SELinux enabled. Please do not run untrusted code without activating SELinux.
