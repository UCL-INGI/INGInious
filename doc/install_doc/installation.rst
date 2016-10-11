Installation and deployment
===========================

Supported platforms
-------------------

INGInious is primarily intended to run on Linux (kernel 3.10+), but it is also compatible with Windows 7+ and OS X 10.9+ thanks to
the Docker toolbox.

Supported Linux distribution includes CentOS 7.x (*recommended OS to run INGInious*), Fedora 22+ and Ubuntu 14.04+.

Dependencies (not including Pipy packages)
------------------------------------------

INGInious needs

- Python_ 3.5+  (not compatible with Python 2.X or Python 3.4)
- Pip
- Docker_ 1.12+
- MongoDB_
- Libtidy
- LibZMQ

.. _Docker: https://www.docker.com
.. _Python: https://www.python.org/
.. _MongoDB: http://www.mongodb.org/

Installation of the dependencies
--------------------------------

Centos 7.0+, Fedora 22+
```````````````````````

The first thing to do is to install Docker. All the informations are available here: `Fedora <https://docs.docker
.com/engine/installation/linux/fedora/>`, `CentOS <https://docs.docker.com/engine/installation/linux/centos/>`.

You then have to install some dependices of INGInious:
::

    $ sudo yum install -y epel-release https://centos7.iuscommunity.org/ius-release.rpm #CentOS only
    $ sudo yum install -y git mongodb mongodb-server gcc libtidy python35u python35u-pip python35u-devel zeromq-devel

.. note::

    You may also add ``openldap-devel`` if you want to use the LDAP auth plugin

You can now start the services ``mongod`` and ``docker``:

::

    $ sudo service mongod start
    $ sudo service docker start

To start them on system startup, use these commands:

::

    $ sudo chkconfig mongod on
    $ sudo chkconfig docker on

Ubuntu 14.04+
`````````````

.. DANGER::
    The tutorial for Ubuntu is not up-to-date. It does not reflect the recent change to Python 3. Help wanted!

Please note that while CentOS, OS X and Windows are used to develop/test/use INGInious everyday, this is not the case for Ubuntu; less support will
be given for this OS.

::

    $ sudo apt-get update
    $ sudo apt-get install git mongodb docker python gcc python-dev pip

.. note::

    You may also add ``libldap2-dev libsasl2-dev libssl-dev`` if you want to use the LDAP auth plugin)

You can then start the services ``mongod`` and ``docker``:

::

    $ sudo initctl mongodb start
    $ sudo initctl docker start

To start them on system startup, use these commands:

::

    $ sudo chkconfig mongod on
    $ sudo chkconfig docker on

OS X 10.9+
``````````

We use brew_ to install some packages. Packages are certainly available too via macPorts.

.. _brew: http://brew.sh/

::

    $ brew install mongodb
    $ brew install python3

Follow the instruction of brew to enable mongodb.

The next step is to install `Docker for Mac <https://docs.docker.com/docker-for-mac/>`.

Windows 7+
``````````

.. DANGER::
    The tutorial for Windows is not up-to-date. It does not reflect the recent change to Python 3. Help wanted!

Download and install Python_, Docker_Toolbox_ and MongoDB_.


A docker machine (use the docker quickstart terminal) and MongoDB must be running to run INGInious. To run MongoDB as a service, please refer to th
appropriate documentation.

.. _Installpip:

Installation of INGInious
-------------------------

Pip+Git
```````

This is the recommended method of installation. It will allow you to use the last development revision of INGInious (as INGInious is a relatively
recent project, it is better to use dev version, which have a lot more functionnalities and bugfixes than old beta version from pipy).

::

    $ pip install --upgrade git+https://github.com/UCL-INGI/INGInious.git

Run the same command to upgrade.

.. note::

   If you plan to use INGInious in production, you may want to enable the LDAP plugin or use CGI instead of the web.py default webserver.
   In this case, you have to install more packages: simply add ``[cgi]``, ``[ldap]`` or ``[cgi,ldap]`` to the above command, depending on your needs:

   ::

       $ pip install --upgrade git+https://github.com/UCL-INGI/INGInious.git[cgi,ldap]


Pip+Pipy
````````

You can install a somewhat beta version from pipy. Please note that as INGInious is still a young project, you may have more problems with the
version from pipy than with the development version.

::

    $ pip install --upgrade inginious

Run the same command to upgrade.

.. note::

    See the note above if you plan to use CGI or LDAP.

Git
```

You can also clone INGInious manually. This is the recommended setup for developpers.

::

    $ git clone https://www.github.com/UCL-INGI/INGInious.git

To update, run

::

    $ git pull

You may need to add some tools to your PATH.

.. _config:

Configuring and starting INGInious
----------------------------------

INGInious comes with two frontends:

.. _LTI Frontend:

* The LTI frontend, which allows to interface with Learning Management System via the LTI_ specification. Any LMS supporting LTI_ is compatible.
  This includes Moodle, edX and Coursera, among many others.

.. _LTI: http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html
.. _Web App:

* The Web App, a mini-LMS made for on-site courses. It offers statistics, group management, and the INGInious Studio, that allows to modify and
  test your tasks directly in your browser.

You can use one, or both. Each of them have to be configured independently, with the commands

::

    $ inginious-install lti
    $ # or ...
    $ inginious-install webapp

Run one (or both) of these commands in the directory that will become the INGInious root directory.
Follow the on-screen instructions.

Once this is done, you can run your frontend:

::

    $ inginious-lti
    $ #or ...
    $ inginious-webapp

This will open a small Python web server and display the url on which it is bind in the console.

If you use the LTI frontend, you have to add it to your LMS: follow the instructions in :ref:`configure_LTI`.

.. _production:
.. _lighttpd:

Using lighttpd (on CentOS 7.0)
------------------------------

In production environments, you can use lighttpd in replacement of the built-in Python server.
This guide is made for CentOS 7.0.

Install lighttpd with fastcgi:

::

    $ sudo yum install lighttpd lighttpd-fastcgi

Put the lighttpd user in the necessary groups, to allow it to launch new containers and to connect to mongodb:

::

    $ usermod -aG docker lighttpd
    $ usermod -aG mongodb lighttpd

Create a folder for INGInious, for example /var/www/INGInious, and allow lighttpd to do whatever he wants inside:

::

    $ mkdir -p /var/www/INGInious
    $ chown -R lighttpd:lighthttpd /var/www/INGInious

Now, Run the ``inginious-install`` command (see :ref:`config`).
Next, create a file named ``start-webapp.sh``, run ``chmod +x`` on it, and put inside:

::

    #! /bin/bash
    cd /var/www/INGInious
    inginious-webapp

Replace ``webapp`` by ``lti`` if you want to use the LTI frontend.

Once this is done, we can configure lighttpd. First, the file */etc/lighttpd/lighttpd.conf*. Modify the document root:

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

    alias.url = (
        "/static/webapp/" => "/usr/lib/python2.7/site-packages/inginious/frontend/webapp/static/",
        "/static/common/" => "/usr/lib/python2.7/site-packages/inginious/frontend/common/static/"
    )

    fastcgi.server = ( "/inginious-webapp" =>
        (( "socket" => "/tmp/fastcgi.socket",
            "bin-path" => "/var/www/INGInious/start-webapp.sh",
            "max-procs" => 1,
            "bin-environment" => (
                "REAL_SCRIPT_NAME" => "",
                "DOCKER_HOST" => "tcp://192.168.59.103:2375"
            ),
            "check-local" => "disable"
        ))
    )

    url.rewrite-once = (
        "^/(.*)$" => "/inginious-webapp/$1",
        "^/favicon.ico$" => "/static/common/favicon.ico",
    )

Replace ``webapp`` by ``lti`` if you want to use the `LTI frontend`_.

Please note that the ``DOCKER_HOST`` env variable is only needed if you use the ``backend=local`` option. It should reflect your current
configuration. To know the value to set, start a terminal that has access to the docker daemon (the terminal should be able to run ``docker info``)
, and write ``$ echo $DOCKER_HOST``. If it returns nothing, just drop the line ``"DOCKER_HOST" => "tcp://192.168.59.103:2375"`` from the
configuration of Lighttpd. Else, put the value return by the command in the configuration. It is possible that may need to do the same for the env
variable ``DOCKER_CERT_PATH`` and ``DOCKER_TLS_VERIFY`` too.

Finally, start the server:

::

    $ sudo chkconfig lighttpd on
    $ sudo service lighttpd start


Using Apache (on CentOS 7.0)
----------------------------

You may also want to use Apache. You should install `mod_wsgi`.
WSGI interfaces are supported through `inginious-webapp` and `inginious-lti` scripts.
Due to limitations in the way that Apache passes environment variables to WSGI
scripts (after requests), **these scripts need to be modified** to indicate the configuration files and the
code path for your installation.

You will need to add user `apache` to the docker group.

The following Apache configuration is suitable to run e.g. the LTI service
assuming the source repository is in `/var/www/INGInious`.

::

    WSGIPythonPath /var/www/INGInious/
    
    # This is a desired solution, but does not work.
    # See https://gist.github.com/GrahamDumpleton/b380652b768e81a7f60c
    # for alternate solutions
    
    #SetEnv INGInious_CONFIG_LTI /var/www/INGInious/configuration.lti.yaml
    #SetEnv INGInious_PATH_LTI /var/www/INGInious/
    
    Listen 8080
    <VirtualHost *:8080>
        ServerName yourhost.com
        Redirect temp / https://yourhost.com:8443/
    </VirtualHost>
    
    Listen 8443
    <VirtualHost *:8443>
    
        ServerName yourhost.com
        ServerAdmin help@yourhost.com
    
        WSGIDaemonProcess inginious-lti user=apache group=apache threads=5
        WSGIProcessGroup inginious-lti
        WSGIScriptAlias / /var/www/INGInious/inginious-lti
        WSGIScriptReloading On
    
        Alias /static/common /var/www/INGInious/inginious/frontend/common/static
        Alias /static/webapp /var/www/INGInious/inginious/frontend/webapp/static
        Alias /static/lti /var/www/INGInious/inginious/frontend/lti/static
    
        AddType text/html .py
    
        <Directory /var/www/INGInious>
            Order deny,allow
                  Allow from all
            </Directory>
    
        # This is necessary to prevent logging to Inginious usernames/passwords
      	# from clients makign reeusts to the token.php endpoint (e.g. Inginious
            # Android App, COG, etc)
    	SetEnvIf Request_URI "token.php" dontlog
    
        ErrorLog /var/log/httpd/inginious-lti-error-ssl.log
        CustomLog /var/log/httpd/inginious-lti-access-ssl.log combined env=!dontlog
        CustomLog /var/log/httpd/inginious-lti-request-ssl.log \
    	          "%t %h %{SSL_PROTOCOL}x %{SSL_CIPHER}x \"%r\" %b" \
    		  env=!dontlog
    
        SSLEngine on
        SSLCertificateFile      /etc/ssl/your.crt
        SSLCertificateChainFile /etc/ssl/your.chain
        SSLCertificateKeyFile   /etc/ssl/your.key
    
        SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown
    		  
        ServerSignature On
    
    </VirtualHost>
    
    # vim: syntax=apache ts=4 sw=4 sts=4 sr noet
