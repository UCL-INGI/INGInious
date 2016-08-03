Configuration reference
=======================

(Note: the best way to configure INGInious is to use ``inginious-install``. See :ref:`config`.)

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

``backend``
    The link to the backend used. You can either set it to ``local`` or indicate the address of your manually-managed backend.

    - ``local``. In this mode, which is the default, you have to ensure the docker daemon is local to your machine, or, at least, share the same
      directory structure. This is typically the case if you use Linux and have a local Docker daemon, or if you use Docker for Mac/Windows, or even
      docker-machine with local machines. This is the configuration described in this tutorial. You will need a running docker daemon on your machine
      for this to work. If you can use any Docker client command, like ``docker info``, INGInious should run flawlessly.

      In this mode, a supplementary config option is available, ``local-config``.

    - ``tcp://xxx.yyy.zzz.aaa:bbbb``, ``udp://xxx.yyy.zzz.aaa:bbbb`` or ``ipc:///path/to/your/sock``, where the adresses are the ip/socket path of
      the backend you started manually. This is for advanced users only. See commands ``inginious-backend`` and ``inginious-agent`` for more
      information.

``local-config``
    These configuration options are available only if you set ``backend:local``.

    ``concurrency``
        Number of concurrent task that can be run by INGInious. By default, it is the number of CPU in your host.

    ``debug_host``
        Host to which the users should connect in order to access to the debug ssh for containers. Most of the time, just do not indicate this
        option: the address will be automagically guessed.

    ``debug_ports``
        Range of port, in the form ``64100-64200``, to which INGInious can bind SSH debug containers, to allow remote debugging. By default, it is
        ``64100-64200``.

    ``tmp_dir``
        A directory whose absolute path must be available by the docker daemon and INGInious at the same time. By default, it is ``./agent_tmp``.

``webterm``
    Address of a INGInious-xterm app (see INGInious-xterm on GitHub). If set, it allows to use in-browser task debug via ssh.
    You have to configure INGInious-xterm according to your configuration of ``local-config.debug_host`` and ``local-config.debug_ports`` or in
    your agent, in order to make the system work properly. Note that if your run the frontend in HTTPS, INGInious-xterm should also run in HTTPS.

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
