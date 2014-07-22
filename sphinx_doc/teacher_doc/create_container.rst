Creating a new container
========================

Creating new containers mainly consists on adding new packages to the *default* container.
The *default* container is built on CentOS 7, and uses *yum* (*rpm*) as package manager. 

Documentation about creating new containers is available on the website of Docker_.
Remember to **always** make your container inherit the *default* container. 

Here is an example of Dockerfile for a container that can launch PHP code:
::
	
	# DOCKER-VERSION 1.1.0

	#inherit from the default container, which have all the needed script to launch tasks
	FROM    inginious/default

	# Add php
	RUN     yum -y install php-cli


.. _Docker: https://www.docker.com/