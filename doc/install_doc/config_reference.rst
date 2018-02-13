.. _ConfigReference:

Configuration reference
=======================

.. HINT::
    The best way to configure INGInious is to use ``inginious-install``. See :ref:`config`.

Configuring INGInious is done via a file named ``configuration.yaml`` or ``configuration.lti.yaml``.
To get started, files named ``configuration.example.yaml`` and ``configuration.lti.example.yaml`` are provided.

.. literalinclude:: ../../configuration.example.yaml
    :language: yaml
    :linenos

The different entries are :

``allow_deletion``
    ``false`` if users cannot delete their accounts (and all related data from database), ``true``otherwise.

``allow_registration``
    ``false`` if database registration should be disabled. In this mode no password can be set and accounts
    are only created via the external authentication systems. ``true`` otherwise.

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

``backup_directory``
    Path to the directory where are courses backup are stored in cases of data wiping.

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

``log_level``
    Can be set to ``INFO``, ``WARN``, or ``DEBUG``. Specifies the logging verbosity.

``maintenance``
    Set to ``true`` if the webapp must be disabled.

``mongo_opt``
    MongoDB client configuration.

    ``host``
        MongoDB server address. If your database is user/password-protected, use the following syntax:
        ``mongodb://USER:PASSWORD@HOSTNAME/DB_NAME``

    ``database``
        You can change the database name if you want multiple instances or in the case of conflict.

``plugins``
    A list of plugin modules together with configuration options.
    See :ref:`plugins` for detailed information on available plugins, including their configuration.
    Please note that the usage of at least one authentication plugin is mandatory for the webapp.

``smtp``
    Mails can be sent by plugins.

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

``static_directory``
    Path to the directory where YAML-defined static pages are located.

`superadmins``
    A list of super-administrators who have admin access on the whole stored content.

``tasks_directory``
    The path to the directory that contains all the task definitions, grouped by courses.
    (see :ref:`task`)

``use_minified_js``
    Set to ``true`` to use the minified version of Javascript scripts, ``false`` otherwise.

``webterm``
    Link to the INGInious xterm app with the following syntax: ``http[s]://host:port``.
    If set, it allows to use in-browser task debug via ssh. (See :ref:`_webterm_setup` for
    more information)

.. _configuration.example.yaml: https://github.com/UCL-INGI/INGInious/blob/master/configuration.example.yaml
.. _docker-py API: https://github.com/docker/docker-py/blob/master/docs/api.md#client-api

.. _plugins:

Plugins
-------

Several plugins are available to complete the INGInious feature set.

External authentication plugins
```````````````````````````````

You need at least one auth plugin activated.

ldap_auth
!!!!!!!!!

Uses an LDAP server to authenticate users.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.auth.ldap_auth
          id: some_id_for_ldap
          host: "your.ldap.server.com"
          encryption: "ssl" #can be tls or none
          base_dn: "ou=People,dc=info,dc=ucl,dc=ac,dc=be"
          request: "(uid={})",
          name: "LDAP Login"

Most of the parameters are self-explaining, but:

``id``
    is the authentication method id. It must be alphanumerical and different from other external authentication methods.

``request``
    is the request made to the LDAP server to search the user to authentify. "{}" is replaced by the username indicated by the user.

saml2_auth
!!!!!!!!!!

Uses a SAML2-compliant identity provider (such as Shibboleth IdP) to authenticate users.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.auth.saml2_auth
            strict: true
            sp:
                entityId: "<your_entity_id>"
                x509cert: "<your_cert>"
                privateKey: "<your_private_key>"
            idp:
                entityId: "https://idp.testshib.org/idp/shibboleth"
                singleSignOnService:
                    url: "https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                x509cert: "<idp_cert>"
                additionalX509certs:
                    - "<idp_cert>"
            security:
                 metadataValidUntil: ""
                 metadataCacheDuration: ""
            attributes:
                 cn: "urn:oid:2.5.4.3"
                 email: "urn:oid:1.3.6.1.4.1.5923.1.1.1.6"
                 uid: "urn:oid:0.9.2342.19200300.100.1.1"

Your IdP is required to provide at least attributes corresponding to the username, the complete name and the email address.
Use the ``attributes`` entry for the mapping. The ``additionalX509certs`` is a plugin-specific entry to specify several
certificates in case your IdP is able to use more than one.

This plugin mainly relies on python3-saml_ package and configuration parameters are interoperable.
Please refer to the package documentation for more detailed configuration parameters. The SP Attribute Consuming Service (ACS)
is automatically configured by the plugin.

.. _python3-saml: https://github.com/onelogin/python3-saml/

db_auth
!!!!!!!

Uses the MongoDB database to authenticate users. Provides a basic email-verification based registration and password
recovery. It does not support manual user management yet. The superadmin has to register the same way other users do.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.auth.db_auth
          allow_deletion: true

For mails to be sent by the registration module, you need to configure the ``smtp`` parameter of your configuration
file. `allow_deletion` parameter can be used to specify if users can delete their accounts from INGInious.

Scoreboard plugin (``webapp``)
``````````````````````````````

This plugin allows to generate course/tasks scoreboards. To enable the plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.scoreboard

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

The score used by this plugin for each task must be generated via a key/value custom feedback
(see :ref:`feedback-custom`) using the ``score`` key. Only the *succeeded* tasks are taken into account.

Contests plugin (``webapp``)
````````````````````````````

This plugin allows to manage an ACM/ICPC like contest inside a course between students.
To enable the plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.contests

A new configuration page named *Contest* appears on the administration page. To enable the contest mode, check the
*Enable contest plugin* box on the appropriate course. Please note that the plugin will override the task
accessibility dates.

Simple grader plugin (``webapp``, ``lti``)
``````````````````````````````````````````

This simple grader allows anonymous POST requests without storing submissions in database.

To enable the plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.simple_grader
          courseid : "external"
          page_pattern: "/external"
          return_fields: "^(result|text|problems)$"

- ``courseid`` is the course id you want to expose to the simple grader.

- ``page_pattern`` is the URL at which you want to make the simple grader available.

- ``return_fields`` is a regular expression matching the submission fields that can be returned via the simple grader.

A demonstration POST form will be available at the ``page_pattern`` specified URL.

New synchronized job
!!!!!!!!!!!!!!!!!!!!

External submissions must take the form of a POST request on the url defined by *page_pattern*.
This POST must contains two data field:

- ``taskid``: the task id of the task

- ``input``: the input for the task, in JSON. The input is a dictionary filled with problemid:problem_answer pairs.

The return value will contains the standard return fields of an INGInious inginious.backend job plus a "status" field that will
contain "ok".

If an internal error occurs, it will return a dictionary containing

::

    {
        "status": "error",
        "status_message": "A message containing a simple description of the error"
    }

New asynchronous job
!!!!!!!!!!!!!!!!!!!!

This POST request allows new jobs to be treated asynchronously.
It must contains three data fields:

- ``taskid``: the task id of the task

- ``input``: the input for the task, in JSON. The input is a dictionary filled with problemid:problem_answer pairs.

- ``async``: field that indicate that the job must be launched asynchronously. Only have to be present, content is not read.

The return value will be a dictionnary containing:

::

    {
        "status": "done",
        "jobid": "the jobid of the async job. Will be needed to get the results."
    }

or

::

    {
        "status": "error",
        "status_message": "A message describing the error"
    }

Get status of asynchronous job
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Given a jobid in input (as field of the POST request) and will return either:
::

    {
        "status": "waiting"
    }

or

::

    {
        "status": "error",
        "status_message": "A message describing the error"
    }

or

::

    {
        "status": "done",
        "...":"..."
    }

where ``...`` are the results of the job, as defined in the ``return_fields`` configuration value.

Git Repo plugin (``webapp``, ``lti``)
`````````````````````````````````````
This plugin allows saving submissions history in a Git repository, according to the following path pattern :
``courseid/taskid/username``. The version kept in the head of branch is the latest submission made.

To enable this plugin, add to your configuration file:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.git_repo
          repo_directory: "./repo_submissions"

The ``repo_directory`` parameter specify the path to the repository that must be initialized before configuration.

Task file readers plugin (``webapp``, ``lti``)
``````````````````````````````````````````````
It is possible to store task files in other formats than YAML. **However, these plugins are provided for
retro-compatibility with previous supported formats, which are deprecated. You therefore use these plugins at your own
risks**.

JSON
!!!!

To enable the JSON task file format:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.task_file_readers.json_reader

RST
!!!

To enable the reStructuredText task file format:
::

    plugins:
        - plugin_module: inginious.frontend.plugins.task_file_readers.rst_reader
