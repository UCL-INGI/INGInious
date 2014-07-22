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

	$ sudo yum install mongodb mongodb-server docker
	$ sudo pip install pymongo pytidylib docker-py sh webpy
	
.. _EPEL: https://fedoraproject.org/wiki/EPEL

You can then enable the services *mongod* and *docker*.

::

	$ sudo service mongod start
	$ sudo service docker start

OS X 10.9+
``````````

We use brew_ to install some packages. Packages are certainly available too via macPorts.
We also use docker-osx_ instead of the official Boot2Docker because it allows to mount
local directory flawlessly.

.. _brew: http://brew.sh/
::

	$ brew install mongodb
	$ brew install python
	$ brew install pip
	$ sudo curl https://raw.githubusercontent.com/noplay/docker-osx/1.0.0/docker-osx > /usr/local/bin/docker-osx
	$ sudo chmod +x /usr/local/bin/docker-osx
	$ sudo pip install pymongo pytidylib docker-py sh webpy

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