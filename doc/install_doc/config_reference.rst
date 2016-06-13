Configuration reference
=======================

(Note: this may not be up-to-date. The best way to configure INGInious is to use ``inginious-install``. See :ref:`config`.)

Configuring INGInious is done via a file named ``configuration.yaml``.
To get you started, a file named `configuration.example.yaml <https://github.com/UCL-INGI/INGInious/blob/master/configuration.example.yaml>`_ is provided.
The file contains detailed explanations, and is kept up to date with INGInious, while this documentation may not.

.. literalinclude:: ../../configuration.example.yaml
    :language: yaml
    :linenos

The different entries are :

``tasks_directory``
    The path to the directory that contains all the task definitions, grouped by courses.
    (see :ref:`task`)

``containers``
    A dictionary of docker's container names.
    The key will be used in the task definition to identify the container, and the value must be a valid Docker container identifier.
    Containers for many languages are available on Docker's hub at https://hub.docker.com/u/ingi/.

``backend``
    The type of backend you want to use.
    This defines where the grading containers are run, and how to access them.
    Four backends are available:

    - ``local``. In this mode, the grading containers run on the same machine as the fontend.
      This is the configuration described in this tutorial.
      You will need a running docker daemon on your machine for this to work.
      If you can use any Docker client command, like ``docker info``, INGInious should run flawlessly.

    - ``docker_machine``, that should be used when using Docker Machine 
      (mostly OS X and Windows users, and users with a lot of servers to manage).
      The option ``machines`` should be filled with the list of machines you want to use.

    - ``remote``, that should be used when the frontend and the Docker daemons are not on the same server.
      This includes advanced configurations for scalability (see :doc:`../dev_doc/understand_inginious`)
      and usage on OS X (as the Docker daemon is run in a virtual machine).

      This settings requires you to provide the option ``docker_daemons`` with a list of distant docker daemons.
      Each docker daemon is defined by three things: its hostname, its port and an additional port used to communicate with the backend.
      **All these ports should be available from the backend!**.
      
      Very specific configuration details are possible;
      please read carefully the ``configuration.example.yaml`` for more information.
      
    - ``remote_manual``, allows you to specify manually the host and port of remote grading agents.
      With this option, the agents are not managed by INGInious and should be monitored by external means.

``docker_daemons``
    Only used when ``backend`` is set to ``remote``.

``mongo_opt``
    Quite self-explanatory.
    You can change the database name if you want multiple instances of in the improbable case of conflict.

``plugins``
    A list of plugin modules together with configuration options.
    See :ref:`plugins` for detailed information on available plugins, including their configuration.

.. _configuration.example.yaml: https://github.com/UCL-INGI/INGInious/blob/master/configuration.example.yaml
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
