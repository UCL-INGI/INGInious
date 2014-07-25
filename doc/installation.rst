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

.. _Docker: https://www.docker.com
.. _Docker-py: https://github.com/dotcloud/docker-py
.. _Python: https://www.python.org/
.. _MongoDB: http://www.mongodb.org/
.. _pymongo: http://api.mongodb.org/python/current/
.. _HTMLTidy: http://tidy.sourceforge.net/
.. _PyTidyLib: http://countergram.com/open-source/pytidylib/docs/index.html
.. _SH: http://amoffat.github.io/sh/
.. _Web.py: http://webpy.org/

Installation of the dependencies
--------------------------------

Centos 7.0+
```````````

Don't forget to enable EPEL_.

::

	$ sudo yum install git mongodb mongodb-server docker python-pip gcc python-devel python-ldap
	$ sudo pip install pymongo pytidylib docker-py sh web.py docutils

Some remarks:

- GCC and python-devel are not needed, but allows pymongo to compile C extensions which result in speed improvements.

- python-ldap is only needed if you use the ldap authentication plugin

- (python-)sh and git are dependencies of the submission_repo plugin

- libtidy and pytidylib are only needed if you use htmltidy to check tasks' output

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
	$ brew install pip
	$ sudo curl https://raw.githubusercontent.com/noplay/docker-osx/1.0.0/docker-osx > /usr/local/bin/docker-osx
	$ sudo chmod +x /usr/local/bin/docker-osx
	$ sudo pip install pymongo pytidylib docker-py sh webpy docutils python-ldap

Follow the instruction of brew to enable mongodb.
Each time you have to run INGInious, don't forget to start docker-osx by running

::

	$ docker-osx start

Installation of INGInious
-------------------------

The installation consist on cloning the github repository of INGInious and to start the
frontend:

::
	
	$ git clone https://github.com/INGInious/INGInious.git
	$ cd INGInious
	$ python app_frontend.py

The server will be running on localhost:8080.

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
