Configuration reference
=======================

(Note: this may not be up-to-date. The best way to configure INGInious is to use ``inginious-install``. See :ref:`config`.)

Configuring INGInious is done via a file named ``configuration.yaml``.
To get you started, a file named ``configuration.example.yaml`` is provided.
It content is :

::

    tasks_directory: ./tasks
    containers:
        default: ingi/inginious-c-default
        cpp: ingi/inginious-c-cpp
    backend: local
    # .. or ..
    #backend: remote
    #docker_daemons:
    #  - remote_host: "192.168.59.103"
    #    remote_docker_port: 2375
    #    remote_agent_port: 63456
    # .. or ..
    #backend: docker_machine
    #machines:
    #  - default
    mongo_opt:
        host: localhost
        database: INGInious
    plugins:
      - plugin_module: frontend.plugins.auth.demo_auth
        users:
            test: test

The different entries are :


``tasks_directory``
    The path to the directory that contains all the task definitions, grouped by courses.
    (see :ref:`task`)

``containers``
    A dictionary of docker's container names.
    The key will be used in the task definition to identify the container, and the value must be a valid Docker container identifier.
    The some `pre-built containers`_ are available on Docker's hub.

``backend`` and ``docker_daemons``
	``backend`` is the type of backend you want to use. Three backends are available

	- ``local``, that should be used when the frontend is used on the same machine as the Docker daemon. This is the case if you followed this
	  tutorial and use CentOS or any other Linux distribution.

	  In ``local`` mode, INGInious uses the same environment variables as the Docker client to connect to the daemon. It means that if you can use
	  any Docker client command, like ``docker info``, INGInious should run flawlessly.

    - ``docker_machine``, that should be used when using Docker Machine (mostly OS X and Windows users, and users with a lot of servers to manage)
      the ``machines`` list should be filled with the name of the machines you want to use.

	- ``remote``, that should be used when the frontend and the Docker daemons are not on the same server. This includes advanced configurations
	  for scalability (see :doc:`../dev_doc/understand_inginious`) and usage on OS X (as the Docker daemon is run in a virtual machine).

	  This settings requires an additional one, ``docker_daemons``. It is simply a list of distant docker daemons. Each docker daemon is defined by
	  three things: its hostname, its port and an additional port used to communicate with the backend. **All these ports should be available from
	  the backend!**. Very specific configuration details are possible; please read carefully the ``configuration.example.yaml`` for more information.

	  The configuration for ``docker_daemons`` shown above is the one for boot2docker (which is outdated).
	- ``remote_manual``, that should never be used directly (it's for debugging purposes).

``mongo_opt``
    Quite self-explanatory. You can change the database name if you want multiple instances of in the improbable case of conflict.

``plugins``
    A list of plugin modules together with configuration options.
    See :ref:`plugins` for detailed information on available plugins, including their configuration.

.. _pre-built containers: https://registry.hub.docker.com/search?q=ingi%2Finginious-c-*&searchfield=
.. _docker-py API: https://github.com/docker/docker-py/blob/master/docs/api.md#client-api

.. _plugins:

Plugins
-------

This section presents a short overview of the main plugins available. All the plugins are located in the folder frontend/plugins, and provide extensive documentation in their "init" method.

Auth plugins
````````````
You need at least one auth plugin activated. For now, two are provided by default: auth.demo_auth and auth.ldap_auth.

demo_auth
!!!!!!!!!

Provides a simple authentification method, mainly for demo purposes, with username/password pairs stored directly in the config file.

Example of configuration:
::
	plugins:
	  - plugin_module: frontend.plugins.auth.demo_auth
    	    users:
                username1: "password1"
                username2: "password2"
                username3: "password3"

ldap_auth
!!!!!!!!!

Uses an LDAP server for authenticating users.

Example of configuration:
::
	plugins:
	  - plugin_module: frontend.plugins.auth.ldap_auth
            host: "your.ldap.server.com"
            encryption": "ssl" #can be tls or none
            base_dn: "ou=People,dc=info,dc=ucl,dc=ac,dc=be"
            request: "uid={}",
            prefix: "",
            name: "INGI Login",
            require_cert: true

Most of the parameters are self-explaining, but:

``request``
	is the request made to the LDAP server to search the user to authentify. "{}" is replaced by the username indicated by the user.
``prefix``
	a prefix that will be added in the internal username used in INGInious. Useful if you have multiple auth methods with usernames used in more than one method.

edX plugin
``````````

Note: the edx plugin is deprecated. Use the `LTI frontend`_ instead.

Provides a *passive* grader for edX XQueue. More information is available on the :doc:`edX <./teacher_doc/edX>` page in this documentation.
Here is an example of configuration:
::
	plugins:
	  - plugin_module: frontend.plugins.edx,
            courseid: "LouvainX",
            page_pattern: "/grader"

``courseid``
	courseid is the id of the course that you want to provide to edX.
	(Please note that you can have multiple instances of the edX plugin, allowing you to use it for more than one course)
``page_pattern``:
	pages that will lead to the edX grader. Can be a simple string or a regex. Note that if you use multiple edX plugin instances,
	page_patterns have to be unique.
