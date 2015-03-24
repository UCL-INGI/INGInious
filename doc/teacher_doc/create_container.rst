Creating a new container image
==============================

Creating the Dockerfile
-----------------------

Container images can be viewed as small operating systems with specific software and configuration.
The main force of the container images is that they are very simple to create and modify, using Dockerfiles.

Here is an example of Dockerfile:

::

   # DOCKER-VERSION 1.1.0

   #inherit from the default container, which have all the needed script to launch tasks
   FROM    ingi/inginious-c-default

   # Add php
   RUN     yum -y install php-cli

As easily seen, this Dockerfile creates a new container image that can launch PHP scripts.
The syntax of these Dockerfiles is extensively described on the website of Docker_, 
but we will detail here the most important things to know.

Each Dockerfile used on INGInious most begin with ```FROM    inginious/ingi-c-default```.
This indicates that you take as base for your new image the default image provided with INGInious.
This default image is itself based on CentOS 7, and uses *yum* (*rpm*) as package manager. 
It is already provided with Python and basic commands, and with all the files needed by INGInious to work.

The line ```RUN     yum -y install php-cli``` indicates to Docker that it must run the command ```yum -y install php-cli``` inside the image.
The ```yum``` command is the equivalent of ```apt-get``` (that is the package manager for Debian, Ubuntu and derivates), 
but for Linux distributions that derivates from Fedora, like CentOS. This will install the package ```php-cli```.
Creating new containers mainly consists on adding new packages to the *default* container, so it is probable that your Dockerfile will contain
mostly this type of lines.

Here is a little more advanced Dockerfile, that is used to provide Oz in INGInious:

::

    FROM    ingi/inginious-c-default

    ADD mozart2.rpm /mozart.rpm
    RUN yum -y install emacs tcl tk
    RUN rpm -ivh /mozart.rpm
    RUN rm /mozart.rpm

Again, we can see it inherit from ```ingi/inginious-c-default```. Then, it uses the command ```ADD```, that takes a file
in the current directory of the Dockerfile (here, ```mozart2.rpm```) and copy it inside the container image, here at the path ```/mozart.rpm```.
It then uses three ```RUN``` commands to install the dependencies of Mozart, then install Mozart itself, and then removing the now uneeded rpm.

Dockerfiles can do many more things, read the documentation on the Docker website to know more about the possibilities.

"Compiling" the Dockerfile
--------------------------

Once you have Docker up and running, it is very simple to create a container image from a Dockerfile:

::

    $ cd /path/to/your/dockerfile
    $ docker build -t my_container_image ./

Docker will then launch a container and run the Dockerfile on it, then will save the state of the disk, that is, in fact, the container image.
It can then be used in INGInious as ```my_container_image```. You have to update the file ```configuration.yaml``` to authorize the usage of the new image.

You can also enter directly in the container image to test it in the command line:

::

    $ docker run -t -i --rm my_container_image /bin/bash


Share what you created
----------------------

If you created a Dockerfile for INGInious, feel free to make a pull request in the repository associated: https://github.com/UCL-INGI/INGInious-containers

(and, if you work in INGI, this is the preferred way to have your container on our instance!)


.. _Docker: https://www.docker.com/
