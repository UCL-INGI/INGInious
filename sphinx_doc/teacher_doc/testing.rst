Testing a task
==============

Directly in the container
-------------------------

You can build a container by yourself and test your scripts directly inside the container.
To do so, you have to:

- Download and install Docker_ (on OS X, prefer docker-osx_ over Boot2Docker. docker-osx
  allows to mount local directory which is needed by INGInious)
- Download the source of the containers you use.
- Build all the containers you need by using the command
  ::
  	
  	sudo docker build -t inginious/containerfolder containerfolder
  
  Take care of the dependencies between the containers.
- Now that your container are built, you can now start one:
  ::
  
  	sudo docker run -v ~/taskDirectory:/ro/task -t -i inginious/youcontainer /bin/bash
  	
  Where *~/taskDirectory* is the folder containing your task data.
- You can then play inside the container. You have all powers inside the container.
  Remember that after you quit the container, any data you modified will be lost.
- You can use the *simulate* command (simply enter *simulate* in the console) to test your
  task.

.. _Docker: https://www.docker.com/
.. _docker-osx: https://github.com/noplay/docker-osx

Unit-tests on tasks
-------------------

TODO