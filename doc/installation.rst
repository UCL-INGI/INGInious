Installation and deployment
===========================

Supported platforms
-------------------

INGInious is tested under OS X 10.9 and CentOS 7 but will probably run without problems on any
other Linux distribution and even on Microsoft Windows® (with some adjustments to the
configuration of Boot2Docker).

Dependencies
------------

The backend needs:

- Docker_ 0.11+
- Python_ 2.7+
- Docker-py_
- Docutils

The frontend needs:

- All the backend dependencies
- MongoDB_
- pymongo_
- HTMLTidy_
- PyTidyLib_
- Python's SH_ lib
- Web.py_
- Simple-LDAP_
- PyYAML_

.. _Docker: https://www.docker.com
.. _Docker-py: https://github.com/dotcloud/docker-py
.. _Python: https://www.python.org/
.. _MongoDB: http://www.mongodb.org/
.. _pymongo: http://api.mongodb.org/python/current/
.. _HTMLTidy: http://tidy.sourceforge.net/
.. _PyTidyLib: http://countergram.com/open-source/pytidylib/docs/index.html
.. _SH: http://amoffat.github.io/sh/
.. _Web.py: http://webpy.org/
.. _Simple-LDAP: https://pypi.python.org/pypi/simpleldap/0.8
.. _PyYAML: https://pypi.python.org/pypi/PyYAML/3.11


Installation of the dependencies
--------------------------------

Centos 7.0+
```````````

Don't forget to enable EPEL_.

::

	$ sudo yum install git mongodb mongodb-server docker python-pip gcc python-devel libtidy
	$ sudo pip install pymongo pytidylib docker-py sh web.py docutils simpleldap pyyaml

Some remarks:

- GCC and python-devel are not needed, but allows pymongo to compile C extensions which result in speed improvements.

- simpleldap is only needed if you use the ldap authentication plugin

- (python-)sh and git are dependencies of the submission_repo plugin

- libtidy and pytidylib are only needed if you use htmltidy to check tasks' output or if you use the edX plugin

.. _EPEL: https://fedoraproject.org/wiki/EPEL

You can then start the services *mongod* and *docker*.

::

	$ sudo service mongod start
	$ sudo service docker start

To start them on system startup, use these commands:

::

	$ sudo chkconfig mongod on
	$ sudo chkconfig docker on

OS X 10.9+
``````````

We use brew_ to install some packages. Packages are certainly available too via macPorts.
We also use docker-osx_ instead of the official Boot2Docker because it allows to mount
local directory flawlessly.

.. _brew: http://brew.sh/
.. _docker-osx: https://github.com/noplay/docker-osx

::

	$ brew install mongodb
	$ brew install python
	$ sudo curl https://raw.githubusercontent.com/noplay/docker-osx/1.0.0/docker-osx > /usr/local/bin/docker-osx
	$ sudo chmod +x /usr/local/bin/docker-osx
	$ sudo pip install pymongo pytidylib docker-py sh web.py docutils simpleldap pyyaml

Follow the instruction of brew to enable mongodb.
Each time you have to run INGInious, don't forget to start docker-osx by running

::

	$ docker-osx start

Installation of INGInious
-------------------------

The installation consist on cloning the github repository of INGInious
and to provide configuration option in ``/configuration.yaml``.

::

	$ git clone https://github.com/UCL-INGI/INGInious.git
	$ cd INGInious
	$ cp configuration.example.yaml configuration.yaml

You should now review and tune configuration options in ``configuration.yaml`` according to `Configuring INGInious`_.

Finally, you can start a demo server with the following command.
If you want a robust webserver for production, see :ref:`production`.

::

	$ python app_frontend.py

The server will be running on localhost:8080.


.. _tasks folder:

Configuring INGInious
---------------------

Configuring INGInious is done via a file named ``configuration.yaml``.
To get you started, a file named ``configuration.example.yaml`` is provided.
It content is :

::

    tasks_directory: ./tasks
    containers:
        default: ingi/inginious-c-default
        cpp: ingi/inginious-c-cpp
    docker_instances:
      - server_url: "tcp://192.168.59.103:2375"
    callback_managers_threads: 2
    submitters_processes: 2
    mongo_opt:
        host: localhost
        database: INGInious
    plugins:
      - plugin_module: frontend.plugins.auth.demo_auth
        users:
            test: test
    allow_html: tidy

The different entries are :


``tasks_directory``
    The path to the directory that contains all the task definitions, grouped by courses.
    (see :ref:`task`)

``containers``
    A ditionnary of docker's container names.
    The key will be used in the task definition to identify the container, and the value must be a valid Docker container identifier.
    The some `pre-built containers`_ are available on Docker's hub.


``docker_instances``
    A list of dictionnaries containing the configuration of docker instances.
    Allowed entries are :

    ``server_url``
        The *base_url* of a docker instance. If you run a local instance, you will probably want to change the default value to ``'unix://var/run/docker.sock'``.
        See `docker-py API`_ for detailed information.

    ``max_concurent_jobs``
        Undocumented

    ``max_concurent-hard-jobs``
        Undocumented

``callback_managers_threads``
    Undocumented. ``1`` is certainly a good default for a local server.

``submitters_processes``
    Undocumented. ``1`` is certainly a good default for a local server.

``mongo_opt``
    Quite self-explanatory. You can change the database name if you want multiple instances of in the iprobable case of conflict.

``plugins``
    A list of plugin modules together with configuration options.
    See :ref:`plugins` for detailed information on available plugins, including their configuration.

``allow_html``
    This parameter accepts three options that define if and how HTML values in strings are treated.
    This option applies globally on descriptions, titles and all strings directly displayed.
    By default, all text is supposed to be in reStructuredText format but ``*IsHTML`` options are available in :ref:`course.yaml` and :ref:`task.yaml`.

    ``false``
        HTML is never allowed.

    ``"tidy"``
        HTML will be sanitized by the HTML Tidy library, to ensure that it is well-formed and will not impact the remaining of the document it is included in.

    ``true``
        HTML is always accepted, and never sanitized. (discouraged)

.. _pre-built containers: https://registry.hub.docker.com/search?q=ingi%2Finginious-c-*&searchfield=
.. _docker-py API: https://github.com/docker/docker-py/blob/master/docs/api.md#client-api


.. _production:

Downloading basic containers
----------------------------

Use this command to pull the default container of INGInious. Lots of other containers are available: `pre-built containers`_.

::

	$ docker pull ingi/inginious-c-default
	$ docker pull ingi/inginious-c-cpp
	
If you pull/create additionnal containers, do not forget to add them in the configuration of INGInious.

Using lighttpd (on CentOS 7.0)
------------------------------

In production environments, you can use lighttpd in replacement of the built-in Python server.
This guide is made for CentOS 7.0.

First, don't forget to enable EPEL_.

We can then install lighttpd with fastcgi:

::

	$ sudo yum install lighttpd lighttpd-fastcgi

Now put the INGInious' sources somewhere, like */var/www/INGInious*.

First of all, we need to put the lighttpd user in the necessary groups, to allow it to launch new containers and to connect to mongodb:

::

	$ usermod -aG docker lighttpd
	$ usermod -aG mongodb lighttpd

Allow lighttpd to do whatever he wants inside the sources:

::

	$ chown -R lighttpd:lighthttpd /var/www/INGInious

Now we can configure lighttpd. First, the file */etc/lighttpd/lighttpd.conf*. Modify the document root:

::

	server.document-root = "/var/www/INGInious"

Next, in module.conf, load theses modules:

::

	server.modules = (
		"mod_access",
		"mod_alias"
	)

	include "conf.d/compress.conf"

	include "conf.d/fastcgi.conf"

You can then replace the content of fastcgi.conf with:

::

	server.modules   += ( "mod_fastcgi" )
	server.modules   += ( "mod_rewrite" )

	fastcgi.server = ( "/app_frontend.py" =>
	(( "socket" => "/tmp/fastcgi.socket",
	   "bin-path" => "/var/www/INGInious/app_frontend.py",
	   "max-procs" => 1,
	  "bin-environment" => (
	    "REAL_SCRIPT_NAME" => ""
	  ),
	  "check-local" => "disable"
	))
	)

	url.rewrite-once = (
	  "^/favicon.ico$" => "/static/favicon.ico",
	  "^/static/(.*)$" => "/static/$1",
	  "^/(.*)$" => "/app_frontend.py/$1",
	)

Finally, start the server:

::

	$ sudo chkconfig lighttpd on
	$ sudo service lighttpd start

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
