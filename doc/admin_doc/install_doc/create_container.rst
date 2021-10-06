

Creating a new container image
==============================

Creating the Dockerfile
-----------------------

Container images can be viewed as small operating systems with specific software and configuration.
The main force of the container images is that they are very simple to create and modify, using Dockerfiles.

Here is an example of Dockerfile:

::

   # DOCKER-VERSION 1.1.0

   # Inherit from the default container, which have all the needed script to launch tasks
   FROM    ingi/inginious-c-base

   # Set the environment name for tasks
   LABEL   org.inginious.grading.name="php"

   # Add php
   RUN     yum -y install php-cli

   # Add the php interpreter as run file interpreter (to allow run.php files)
   RUN echo 'run_types["php"] = "/bin/php"' >> /usr/lib/python3.6/site-packages/inginious_container_api/run_types.py

As easily seen, this Dockerfile creates a new container image that can launch PHP scripts.
The syntax of these Dockerfiles is extensively described on the website of Docker_, 
but we will detail here the most important things to know.

Each Dockerfile used on INGInious should begin with ```FROM inginious/ingi-c-base``` and
```LABEL org.inginious.grading.name="some_name"```. The first line indicates that you take as base for your new image
the default image provided with INGInious. This default image is itself based on CentOS 7, and uses *yum* (*rpm*)
as package manager. It is already provided with Python and basic commands, and with all the files needed by INGInious
to work. The second line is used to indicate the environment name (here, ```some_name```) that will be used for tasks.

The line ```RUN yum -y install php-cli``` indicates to Docker that it must run the command ```yum -y install php-cli```
inside the image. The ```yum``` command is the equivalent of ```apt-get``` (that is the package manager for Debian,
Ubuntu and derivates), but for Linux distributions that derivates from Fedora, like CentOS. This will install the package
```php-cli```. Creating new containers mainly consists on adding new packages to the *default* container, so it is
probable that your Dockerfile will contain mostly this type of lines.

Here is a little more advanced Dockerfile, that is used to provide Mozart/Oz in INGInious:

::

    FROM    ingi/inginious-c-base
    LABEL   org.inginious.grading.name="oz"

    ADD mozart2.rpm /mozart.rpm
    RUN yum -y install emacs tcl tk
    RUN rpm -ivh /mozart.rpm
    RUN rm /mozart.rpm

Again, it inherits from ```ingi/inginious-c-base``` and the environment name is set to ```oz```. Then, it
uses the command ```ADD```, that takes a file in the current directory of the Dockerfile (here, ```mozart2.rpm```)
and copy it inside the container image, here at the path ```/mozart.rpm```. It then uses three ```RUN``` commands to
install the dependencies of Mozart, then install Mozart itself, and then removing the now uneeded rpm.

Dockerfiles can do many more things, read the documentation on the Docker website to know more about the possibilities.


.. _new_container:

Compiling the Dockerfile
--------------------------

Once you have Docker up and running, it is very simple to create a container image from a Dockerfile:

::

    $ cd /path/to/your/dockerfile
    $ docker build -t my_container_image ./

Docker will then launch a container and run the Dockerfile on it, then will save the state of the disk, that is,
in fact, the container image. INGInious will automatically detect the environment based on the labels you've set in the
Dockerfile. Therefore, the tag ```my_container_image``` can be set to any value. As a convention, we adopted
```inginious-c-XXX```.

For the new environment to be available, you have to restart INGInious (or, at least, the Docker agent if you are running
INGInious components on separate machines). More details here: https://inginious.org/course/tutorial/12_environments

You can also enter directly in the container image to test it in the command line:

::

    $ docker run -t -i --rm my_container_image /bin/bash


It is also easy to rebuild the initially provided containers images.
If you have a proper INGInious version installed, no need for building images, you can re-download the provided images by simply running:
::
    $ inginious-container-update

If you are running on a dev environment (cloned from the repository), from the main directory, enter the following commands to take into consideration your local files:
::

    $ cd base-containers/base
    $ docker build -t ingi/inginious-c-base ./
    $ cd ../default
    $ docker build -t ingi/inginious-c-default ./

Note, this manual building step should not be necessary for a teacher.
Of course, if you rebuilt your images, you will have to restart inginious-webapp.

Share what you created
----------------------

If you created a Dockerfile for INGInious, feel free to make a pull request in the repository associated: https://github.com/UCL-INGI/INGInious-containers

.. _Docker: https://www.docker.com/
