Updating INGInious
==================

General update procedure
------------------------

Updating INGInious is very simple. Simply update your package, then pull the new images from Docker Hub:

If you installed with pip from git:
```````````````````````````````````

::

    $ pip install --process-dependency-links --upgrade git+https://github.com/UCL-INGI/INGInious.git

If you installed with pip from pipy:
````````````````````````````````````

::

    $ pip install --process-dependency-links --upgrade inginious

If you cloned the sources:
``````````````````````````

::

    $ cd INGInious_dir
    $ git pull

Updating your containers:
`````````````````````````

::

    $ docker images | awk -F " " '{print $1}' | grep "ingi/inginious-c" | xargs -n 1 docker pull

Updating the configuration
--------------------------

Most of the time, you won't need to update your configuration; it will only be necessary when an huge architectural change is made on INGInious.

Updating from INGInious 0.2 (< August 2015) to INGInious 0.3+
`````````````````````````````````````````````````````````````

As INGInious is now packaged using setuptools, the best thing to do is to remove the sources of INGInious, install it with pip, and configure it
again with ``inginious-install``.

Please see :ref:`Installpip`.

Note that the edX plugin is deprecated in favor of the new LTI frontend. Again, see :ref:`Installpip` for more informations.

Updating from INGInious 0.1 (< June 2015) to INGInious 0.2
``````````````````````````````````````````````````````````

If you are on Linux (here, Centos 7), and runs INGInious on the same machine as the Docker daemon
#################################################################################################

Remove the options
::

    docker_instances:
      - server_url: "tcp://192.168.59.103:2375"
      # ...
    callback_managers_threads: 2
    submitters_processes: 2

and replace them by

::

    backend: local

Be sure that the environment variable for the docker client (DOCKER_HOST) are correctly defined when you call INGInious.
You may have to update the configuration of Lighttpd (if you use it) to add the DOCKER_HOST env variable (see :ref:`lighttpd`).

If you use OS X or you use remote Docker daemons
################################################

Add to your configuration

::

    backend: remote

Delete these:

::

    callback_managers_threads: 2
    submitters_processes: 2

then, modify the ``docker_instances`` option, that was in the form

::

    docker_instances:
      - server_url: "tcp://192.168.59.103:2375"
      # ...

to transform it in the form of

::

    docker_daemons:
      - remote_host: "192.168.59.103"
        remote_docker_port: 2375
        remote_agent_port: 63456

Verify that the port 63456 is open on the remote docker host.
Please take a look at the file ``configuration.example.yaml`` for more information.