.. _ConfigReference:

Configuration reference
=======================

(Note: the best way to configure INGInious is to use ``inginious-install``. See :ref:`config`.)

Configuring INGInious is done via a file named ``configuration.yaml`` or ``configuration.lti.yaml``.
To get started, files named ``configuration.example.yaml`` and ``configuration.lti.example.yaml`` are provided.

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
        option: the address will be automatically guessed.

    ``debug_ports``
        Range of port, in the form ``64100-64200``, to which INGInious can bind SSH debug containers, to allow remote debugging. By default, it is
        ``64100-64200``.

    ``tmp_dir``
        A directory whose absolute path must be available by the docker daemon and INGInious at the same time. By default, it is ``./agent_tmp``.

``mongo_opt``
    MongoDB client configuration.

    ``host``
        MongoDB server address. If your database is user/password-protected, use the following syntax:
        ``mongodb://USER:PASSWORD@HOSTNAME/DB_NAME``

    ``database``
        You can change the database name if you want multiple instances or in the case of conflict.

``log_level``
    Can be set to ``INFO``, ``WARN``, or ``DEBUG``. Specifies the logging verbosity.

``use_minified_js``
    Set to ``true`` to use the minified version of Javascript scripts, ``false`` otherwise.

``webterm``
    Link to the INGInious xterm app with the following syntax: ``http[s]://host:port``.
    If set, it allows to use in-browser task debug via ssh. (See :ref:`_webterm_setup` for
    more information)

Webapp-specific configuration
-----------------------------

``superadmins``
    A list of super-administrators who have admin access on the whole stored content.

``maintenance``
    Set to ``true`` if the webapp must be disabled.

``backup_directory``
    Path to the directory where are courses backup are stored in cases of data wiping.

``plugins``
    A list of plugin modules together with configuration options.
    See :ref:`plugins` for detailed information on available plugins, including their configuration.

``smtp``
    Mails can be send by batch containers at the end of the job execution.

    ``sendername``
        Email sender name, e.g. : ``INGInious <no-reply@inginious.org>``

    ``host``
        SMTP server.

    ``port``
        SMTP port.

    ``username``
        SMTP username.

    ``password``
        SMTP password.

    ``starttls``
        Set to ``true`` if TLS is needed.

.. _configuration.example.yaml: https://github.com/UCL-INGI/INGInious/blob/master/configuration.example.yaml
.. _docker-py API: https://github.com/docker/docker-py/blob/master/docs/api.md#client-api

LTI-specific configuration
--------------------------
The LTI interface uses most of the same configuration options as the webapp as well as the following:

``lti``
    A list of LTI consumer key and secret values.

``lti_user_name``
    The LTI field used to identify the user. By default this is `user_id`, which for many LMS system would be
    the numeric ID of the user. It can be set to `ext_user_username` which is often a unique username.

``download_directory``
    The path to the directory where downloads are stored temporarily during the archive is being prepared.

.. _plugins:

Plugins
-------

This section presents a short overview of the main plugins available. All the plugins are located in the folder frontend/plugins, and provide extensive documentation in their "init" method.

Auth plugins
````````````
You need at least one auth plugin activated.

demo_auth
!!!!!!!!!

Provides a simple authentification method, mainly for demo purposes, with username/password pairs stored directly in the config file.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.webapp.plugins.auth.demo_auth
            users:
                username1: "password1"
                username2: "password2"
                username3: "password3"

Each key/value pair in the ``users`` field corresponds to a new username/password user.

ldap_auth
!!!!!!!!!

Uses an LDAP server to authenticate users.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.webapp.plugins.auth.ldap_auth
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

db_auth
!!!!!!!

Uses the MongoDB database to authenticate users. Provides a basic email-verification based registration and password
recovery. It does not support manual user management yet. The superadmin has to register the same way other users do.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.webapp.plugins.auth.db_auth

Scoreboard plugin
`````````````````

This plugin allows to generate course/tasks scoreboards. To enable the plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.webapp.plugins.scoreboard

To define a new scoreboard, an additional field ``scoreboard`` must be defined in the ``course.yaml`` file
associated to a course (See :ref:`course`). For instance:
::

    scoreboard:
        - content: ["taskid1"]
          name: "Scoreboard task 1"
        - content: ["taskid2", "taskid3"] # sum of both score is taken as overall score
          name: "Scoreboard for task 2 and 3"
        - content: {"taskid4": 2, "taskid5": 3} # overall score is 2*score of taskid4 + 3*score of taskid5
          name: "Another scoreboard"
          reverse: True

This defines three scoreboards for the course. The first one will create a scoreboard for task id ``taskid1`` and will
be displayed as ``Scoreboard task 1``. The second one will create a scoreboard for ``taskid2`` and ``taskid3`` where
both scores are added. The last one is more complex and will create a reversed scoreboard for task ``taskid4`` and
``taskid5`` where both scores are wieghted by factor ``2`` and ``3``, respectively.

Please note that the score used by this plugin for each task must be generated via a key/value custom feedback
(see :ref:`feedback-custom`) using the ``score`` key. Only the *succeeded* tasks are taken into account.