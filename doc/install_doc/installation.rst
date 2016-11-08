Installation and deployment
===========================

Supported platforms
-------------------

INGInious is intended to run on Linux (kernel 3.10+), but can also be run on Windows and macOS thanks to
the Docker toolbox.

Dependencies setup
------------------

INGInious needs:

- Python_ (with pip) **3.5+**
- Docker_ 1.12+
- MongoDB_
- Libtidy
- LibZMQ

.. _Docker: https://www.docker.com
.. _Python: https://www.python.org/
.. _MongoDB: http://www.mongodb.org/

RHEL/Cent OS 7.0+, Fedora 24+
`````````````````````````````

The previously mentioned dependencies can be installed, for Cent OS 7.0+ :
::

    # curl -fsSL https://get.docker.com/ | sh #This will setup the Docker repo
    # yum install -y epel-release https://centos7.iuscommunity.org/ius-release.rpm
    # yum install -y git mongodb mongodb-server gcc libtidy python35u python35u-pip python35u-devel zeromq-devel

Or, for Fedora 24+:
::

    # curl -fsSL https://get.docker.com/ | sh #This will setup the Docker repo
    # dnf install -y git mongodb mongodb-server gcc libtidy python3 python3-pip python3-devel zeromq-devel

You may also add ``openldap-devel`` if you want to use the LDAP auth plugin.

.. DANGER::
    Due to compatibility issues, it is recommended to disable SELinux on the target machine.

You can now start and enable the ``mongod`` and ``docker`` services:
::

    # systemctl start mongod
    # systemctl enable mongod
    # systemctl start docker
    # systemctl enable docker

Ubuntu 16.04+
`````````````

The previously mentioned dependencies can be installed, for Ubuntu 16.04+:
::

    # curl -fsSL https://get.docker.com/ | sh #This will setup the Docker repo
    # apt-get install git mongodb gcc tidy python3 python3-pip python3-dev libzmq-dev

You may also add ``libldap2-dev libsasl2-dev libssl-dev`` if you want to use the LDAP auth plugin)

You can now start and enable the ``mongod`` and ``docker`` services:
::

    # systemctl start mongodb
    # systemctl enable mongodb
    # systemctl start docker
    # systemctl enable docker

OS X 10.9+
``````````

We use brew_ to install some packages. Packages are certainly available too via macPorts.

.. _brew: http://brew.sh/

::

    $ brew install mongodb
    $ brew install python3

Follow the instruction of brew to enable mongodb.

The next step is to install `Docker for Mac <https://docs.docker.com/docker-for-mac/>`.

Windows
```````

.. DANGER::
    INGInious rely on Docker to run containers. While Docker is supported on Windows 10 (version 1607), INGInious does not
    provide support for Windows containers yet.

The recommended way to run INGInious under Windows is by using a Linux virtual machine, for much more simplicity. One can
also only run the Docker agent under a Linux virtual machine and run the backend and selected frontend under Windows.

In the later case, you'll need to install Python 3.5+, MongoDB, LibTidy and LibZMQ.

.. _Installpip:

Installing INGInious
--------------------

The recommended setup is to install INGInious via pip and the master branch of the INGInious git repository.
This allows you to use the latest development version. This version is currently the supported one for issues.
::

    $ pip3 install --upgrade git+https://github.com/UCL-INGI/INGInious.git

This will automatically upgrade an existing version.

.. note::

   You may want to enable the LDAP plugin or use (F)CGI instead of the web.py default webserver.
   In this case, you have to install more packages: simply add ``[cgi]``, ``[ldap]`` or ``[cgi,ldap]`` to the above command, depending on your needs:

   ::

       $ pip3 install --upgrade git+https://github.com/UCL-INGI/INGInious.git[cgi,ldap]

Some previous releases are also published on Pipy. However, no support is provided for these versions now. To install
the latest previous release:
::

    $ pip install --upgrade inginious

.. _config:

Configuring INGInious
---------------------

INGInious comes with two frontends:

.. _LTI Frontend:

* The LTI frontend, which allows to interface with Learning Management System via the LTI_ specification.
  Any LMS supporting LTI_ is compatible. This includes Moodle, edX and Coursera, among many others.

.. _LTI: http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html
.. _Web App:

* The Web App, a mini-LMS made for on-site courses. It provides statistics, group management, and the INGInious studio,
  that allows to modify and test your tasks directly in your browser.

You can use one, or both. Each of them have to be configured independently. This can be done automatically with the
``inginious-install`` CLI. To configure the LTI frontend:
::

    $ inginious-install lti

To configure the Web App frontend:
::

    $ inginious-install webapp

This will help you create the configuration file in the current directory. For manual configuration and details, see
:ref:`ConfigReference`.

The detailed ``inginious-install`` reference can be found at :ref:`inginious-install`.

Running INGInious
-----------------

During the configuration step, you were asked to setup either a local or remote backend. In the former case, the frontend
will automatically start a local backend and grading agents.

With local backend/agent
````````````````````````
To run the frontend(s), please use the ``inginious-lti`` or ``inginious-webapp`` CLI. This will open a small Python
web server and display the url on which it is bind in the console. Some parameters (configuration file, host, port)
can be specified. Details are available at :ref:`inginious-lti` and :ref:`inginious-webapp`.

If you use the LTI frontend, you have to add it to your LMS: follow the instructions in :ref:`configure_LTI`.

With remote backend/agent
`````````````````````````

.. _production:
.. _lighttpd:


Using lighttpd (on CentOS 7.x)
------------------------------

In production environments, you can use lighttpd in replacement of the built-in Python server.
This guide is made for CentOS 7.x.

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
        "/static/webapp/" => "/usr/lib/python3.5/site-packages/inginious/frontend/webapp/static/",
        "/static/common/" => "/usr/lib/python3.5/site-packages/inginious/frontend/common/static/"
    )

    fastcgi.server = ( "/inginious-webapp" =>
        (( "socket" => "/tmp/fastcgi.socket",
            "bin-path" => "inginious-webapp",
            "max-procs" => 1,
            "bin-environment" => (
                "INGINIOUS_WEBAPP_HOST" => "0.0.0.0",
                "INGINIOUS_WEBAPP_PORT" => 80,
                "INGINIOUS_WEBAPP_CONFIG" => "/var/www/INGInious/configuration.yaml",
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

In this configuration file, some environment variables are passed.

- The ``DOCKER_HOST`` env variable is only needed if
  you use the ``backend=local`` option. It should reflect your current configuration. To know the value to set, start a
  terminal that has access to the docker daemon (the terminal should be able to run ``docker info``), and write ``$ echo $DOCKER_HOST``.
  If it returns nothing, just drop the line ``"DOCKER_HOST" => "tcp://192.168.59.103:2375"`` from the
  configuration of lighttpd. Otherwise, put the value return by the command in the configuration. It is possible
  that may need to do the same for the env variable ``DOCKER_CERT_PATH`` and ``DOCKER_TLS_VERIFY`` too.
- The ``INGINIOUS_WEBAPP`` or ``INGINIOUS_LTI`` (according to your config) prefixed environment variables are used to
  replace the default command line parameters.

Finally, start the server:

::

    $ sudo chkconfig lighttpd on
    $ sudo service lighttpd start


Using Apache (on CentOS 7.x)
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
    
    #SetEnv INGINIOUS_LTI_CONFIG /var/www/INGInious/configuration.lti.yaml
    
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
