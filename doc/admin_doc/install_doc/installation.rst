Installation and deployment
===========================

Supported platforms
-------------------

INGInious is intended to run on Linux (kernel 3.10+), but can also be run on macOS thanks to the Docker toolbox.

.. NOTE::

    While Docker is supported on Windows 10, INGInious does not provide support for Windows yet. If you are willing to
    contribute this, feel free to contact us on Github.

Dependencies setup
------------------

INGInious needs:

- Python_ 3
- Docker_
- MongoDB_
- Libtidy
- LibZMQ

.. _Docker: https://www.docker.com
.. _Python: https://www.python.org/
.. _MongoDB: http://www.mongodb.org/

RHEL/Cent OS 7+, Fedora 32+
`````````````````````````````

.. DANGER::
    Due to compatibility issues, it is recommended to disable SELinux on the target machine.

The previously mentioned dependencies can be installed, for Cent OS 7+ :

.. code-block:: bash

    # yum install -y epel-release
    # yum install -y git gcc libtidy python3 python3-devel python3-pip zeromq-devel yum-utils
    # yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    # yum install -y docker-ce docker-ce-cli
    # cat <<EOF > /etc/yum.repos.d/mongodb-org-4.4.repo
    [mongodb-org-4.4]
    name=MongoDB Repository
    baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/4.4/x86_64/
    gpgcheck=1
    enabled=1
    gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
    EOF
    # yum install -y mongodb-org mongodb-org-server

Or, for Fedora 32+:

.. code-block:: bash

    # yum install -y git gcc libtidy python3 python3-devel python3-pip zeromq-devel dnf-plugins-core
    # dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    # dnf install -y docker-ce docker-ce-cli
    # cat <<EOF > /etc/yum.repos.d/mongodb-org-4.4.repo
    [mongodb-org-4.4]
    name=MongoDB Repository
    baseurl=https://repo.mongodb.org/yum/redhat/8/mongodb-org/4.4/x86_64/
    gpgcheck=1
    enabled=1
    gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
    EOF
    # yum install -y mongodb-org mongodb-org-server

You may also add ``xmlsec1-openssl-devel libtool-ltdl-devel`` for the SAML2 auth plugin.

You can now start and enable the ``mongod`` and ``docker`` services:
::

    # systemctl start mongod
    # systemctl enable mongod
    # systemctl start docker
    # systemctl enable docker
    
Ubuntu 18.04+
`````````````

The previously mentioned dependencies can be installed, for Ubuntu 18.04+:

.. code-block:: bash

    # apt-get update
    # apt-get install git gcc tidy python3 python3-pip python3-dev libzmq3-dev mongodb apt-transport-https curl gnupg lsb-release
    # curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    # echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    # apt-get update
    # apt-get install docker-ce docker-ce-cli

You may also add ``libxmlsec1-dev libltdl-dev`` for the SAML2 auth plugin

You can now start and enable the ``mongod`` and ``docker`` services:
::

    # systemctl start mongodb
    # systemctl enable mongodb
    # systemctl start docker
    # systemctl enable docker

macOS
`````

.. WARNING::

    While Docker supports both x86 and ARM containers on Apple silicon, compatibility hasn't been tested yet.
    Feel free to contribute.

We use brew_ to install some packages. Packages are certainly available too via macPorts.

.. _brew: http://brew.sh/

::

    $ brew install mongodb
    $ brew install python3

Follow the instruction of brew to enable mongodb.

The next step is to install `Docker for Mac <https://docs.docker.com/docker-for-mac/install/>`_.

.. _Installpip:

Installing INGInious
--------------------

The recommended setup is to install INGInious via pip and the master branch of the INGInious git repository.
This allows you to use the latest development version. This version is currently the supported one for issues.
::

    $ pip3 install --upgrade git+https://github.com/UCL-INGI/INGInious.git@inginious-0.8

This will automatically upgrade an existing version.

.. note::

   You may want to enable the LDAP/SAML2 plugin or use FCGI/UWSGI instead of the web.py default webserver.
   In this case, you have to install more packages: simply add ``[cgi]``, ``[uwsgi]``, ``[ldap]`` or ``[saml2]`` to the above command, depending on your needs:

   ::

       $ pip3 install --upgrade git+https://github.com/UCL-INGI/INGInious.git@inginious-0.8#egg=INGInious[cgi,ldap]

.. _config:

Configuring INGInious
---------------------

INGInious comes with a mini-LMS web app that provides statistics, group management, and the
INGInious studio, that allows to modify and test your tasks directly in your browser. It supports the LTI_ interface
that allows to interface with Learning Management System via the LTI_ specification. Any LMS supporting LTI_ is
compatible. This includes Moodle, edX, among many others.

.. _LTI: http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html

It is recommended to create a folder for INGInious and subfolders for tasks and backup, e.g.:
::

    $ mkdir -p /var/www/inginious
    $ cd /var/www/inginious
    $ mkdir tasks
    $ mkdir backup

To configure the web app automatically, use the ``inginious-install`` CLI.

::

    $ inginious-install

This will help you create the configuration file in the current directory. 
When asked about the tasks folder, enter an absolute folder: /var/www/inginious/tasks .
Similarly, when asked about the backup folder, enter an absolute folder: /var/www/inginious/backup .

For manual configuration and details, see
:ref:`ConfigReference`. 
In particular, make sure to add smtp configuration into your `configuration.yaml` file, since INGInious must send email during new user registration.

The detailed ``inginious-install`` reference can be found at :ref:`inginious-install`.

Running INGInious
-----------------

During the configuration step, you were asked to setup either a local or remote backend. In the former case, the frontend
will automatically start a local backend and grading agents.
Additionally, if you intend to have many simultaneous submissions, it is highly recommended to have a webserver, such as lighttpd or Apache -- see below.

With local backend/agent -- no webserver
````````````````````````````````````````
To run the frontend, please use the ``inginious-webapp`` CLI. This will open a small Python
web server and display the url on which it is bind in the console. Some parameters (configuration file, host, port)
can be specified. Details are available at :ref:`inginious-webapp`.

With remote backend/agent -- no webserver
`````````````````````````````````````````
To run INGInious with a remote backend (and agents), do as follows:

#. On the backend host, launch the backend (see :ref:`inginious-backend`) :
   ::

        inginious-backend tcp://backend-host:2001 tcp://backend-host:2000

   The agents will connect on ``tcp://backend-host:2001`` and clients on ``tcp://backend-host:2000``
#. Possibly on different hosts, launch the Docker and MCQ agents (see :ref:`inginious-agent-docker`
   and :ref:`inginious-agent-mcq`) :
   ::

        inginious-agent-docker tcp://backend-host:2001
        inginious-agent-mcq tcp://backend-host:2001
#. In your INGInious frontend configuration file (see :ref:`ConfigReference`), set ``backend`` to :
   ::

        backend: tcp://backend-host:2000
#. Run the frontend using :ref:`inginious-webapp`.
   ::

         inginious-webapp --config /path/to/configuration.yaml

.. _production:

With local backend/agent and a webserver
````````````````````````````````````````

The following guides suggest to run the INGInious webapp on http port and WebDAV on port 8080 on the same host.
You are free to adapt them to your use case (for instance, adding SSL support or using two hostnames).

.. _lighttpd:

.. WARNING::
    In configurations below, environment variables accessible to the application must be explicitly repeated.
    **If you use a local backend with remote Docker daemon**, you may need to set the ``DOCKER_HOST`` variable.
    To know the value to set, start a terminal that has access to the docker daemon (the terminal should be able to run
    ``docker info``), and write ``echo $DOCKER_HOST``. If it returns nothing, just ignore this comment. It is possible
    that you may need to do the same for the env variable ``DOCKER_CERT_PATH`` and ``DOCKER_TLS_VERIFY`` too.

Using lighttpd
``````````````

In production environments, you can use lighttpd in replacement of the built-in Python server.
This guide is made for CentOS 7.x.

Install lighttpd with fastcgi:

::

    # yum install lighttpd lighttpd-fastcgi

Add the ``lighttpd`` user in the necessary groups, to allow it to launch new containers and to connect to mongodb:

::

    # usermod -aG docker lighttpd
    # usermod -aG mongodb lighttpd

Create a folder for INGInious, for example ``/var/www/INGInious``, and change the directory owner to ``lighttpd``:

::

    # mkdir -p /var/www/INGInious
    # chown -R lighttpd:lighttpd /var/www/INGInious

Put your configuration file in that folder, as well as your tasks, backup, download, and temporary (if local backend)
directories (see :ref:`config` for more details on these folders).

Once this is done, we can configure lighttpd. First, the file ``/etc/lighttpd/modules.conf``, to load these modules:
::

    server.modules = (
        "mod_access",
        "mod_alias"
    )

    include "conf.d/compress.conf"
    include "conf.d/fastcgi.conf"

You can then add virtual host entries in a ``/etc/lighttpd/vhosts.d/inginious.conf`` file and apply the following rules:
::

    server.modules   += ( "mod_fastcgi" )
    server.modules   += ( "mod_rewrite" )

    $SERVER["socket"] == ":80" {
        alias.url = (
            "/static/" => "/usr/lib/python3.6/site-packages/inginious/frontend/static/"
        )

        fastcgi.server = ( "/inginious-webapp" =>
            (( "socket" => "/tmp/fastcgi.socket",
                "bin-path" => "/usr/bin/inginious-webapp",
                "max-procs" => 1,
                "bin-environment" => (
                    "INGINIOUS_WEBAPP_HOST" => "0.0.0.0",
                    "INGINIOUS_WEBAPP_PORT" => "80",
                    "INGINIOUS_WEBAPP_CONFIG" => "/var/www/INGInious/configuration.yaml",
                    "REAL_SCRIPT_NAME" => ""
                ),
                "check-local" => "disable"
            ))
        )

        url.rewrite-once = (
            "^/favicon.ico$" => "/static/icons/favicon.ico",
            "^/static/(.*)$" => "/static/$1",
            "^/(.*)$" => "/inginious-webapp/$1"
        )
    }

    $SERVER["socket"] == ":8080" {
        fastcgi.server = ( "/inginious-webdav" =>
            (( "socket" => "/tmp/fastcgi.socket",
                "bin-path" => "/usr/bin/inginious-webdav",
                "max-procs" => 1,
                "bin-environment" => (
                    "INGINIOUS_WEBDAV_HOST" => "0.0.0.0",
                    "INGINIOUS_WEBDAV_PORT" => "8080",
                    "INGINIOUS_WEBAPP_CONFIG" => "/var/www/INGInious/configuration.yaml",
                    "REAL_SCRIPT_NAME" => ""
                ),
                "check-local" => "disable"
            ))
        )

        url.rewrite-once = (
            "^/(.*)$" => "/inginious-webdav/$1"
        )
    }


In your lighttpd configuration  ``/etc/lighttpd/lighttpd.conf`` change these lines:
::

   server.document-root = server_root + "/INGInious"

Also append this at the end of ``/etc/lighttpd/lighttpd.conf``:

  ::

   include "/etc/lighttpd/vhosts.d/inginious.conf"

.. note::

   Make sure that INGInious static directory path is executable by Ligttpd by giving the right permission with ``chmod``

In some cases docker won't be able to run INGInious containers due to invalid temp directory just
make sure you append this in your INGInious configuration.yaml

  ::

   local-config:
       tmp_dir: /var/www/INGInious/agent_tmp

The ``INGINIOUS_WEBAPP`` and ``INGINIOUS_WEBDAV`` prefixed environment variables are used to replace the default command line parameters.
See :ref:`inginious-webapp` for more details.

The ``REAL_SCRIPT_NAME`` environment variable must be specified under lighttpd if you plan to access the application
from another path than the specified one. In this case, lighttpd forces to set a non-root path ``/inginious-webapp``,
while a root access if wanted, in order to serve static files correctly. Therefore, this environment variable is set
to an empty string in addition to the rewrite rule.

.. note::

   The Default configuration doesn't optimize Inginious for performance, please refer to 
   https://redmine.lighttpd.net/projects/lighttpd/wiki/Docs_Performance for more about performance optimising
   you may also change 'max-procs' and append "PHP_FCGI_CHILDREN" => "someValue" inside "bin-environment"
   for more about these values check https://redmine.lighttpd.net/projects/lighttpd/wiki/Docs_PerformanceFastCGI
 
   
Finally, start the server:

::

    # systemctl enable lighttpd
    # systemctl start lighttpd

.. _apache:

Using Apache on CentOS 7.x
``````````````````````````

You may also want to use Apache. You should install `mod_wsgi`. WSGI interfaces are supported through the
`inginious-webapp` script.

Install the following packages (please note that the Python3.5+ version of *mod_wsgi* is required):
::

    # yum install httpd httpd-devel
    # pip3.5 install mod_wsgi

Add the ``apache`` user in the necessary groups, to allow it to launch new containers and to connect to mongodb:
::

    # usermod -aG docker apache
    # usermod -aG mongodb apache

Create a folder for INGInious, for example ``/var/www/INGInious``, and change the directory owner to ``apache``:
::

    # mkdir -p /var/www/INGInious
    # chown -R apache:apache /var/www/INGInious

Put your configuration file in that folder, as well as your tasks, backup, download, and temporary (if local backend)
directories (see :ref:`config` for more details on these folders).

Set the environment variables used by the INGInious CLI scripts in the Apache service environment file
(see lighttpd_ for more details):
::

    # cat  << EOF >> /etc/sysconfig/httpd
    INGINIOUS_WEBAPP_CONFIG="/var/www/INGInious/configuration.yaml"
    INGINIOUS_WEBAPP_HOST="0.0.0.0"
    INGINIOUS_WEBAPP_PORT="80"
    EOF
    # rm /etc/httpd/conf.d/welcome.conf

Please note that the service environment file ``/etc/sysconfig/httpd`` may differ from your distribution and wether it
uses *systemd* or *init*.

Append this in your INGInious configuration.yaml

  ::

   local-config:
       tmp_dir: /var/www/inginious/agent_tmp

You can then add virtual host entries in a ``/etc/httpd/vhosts.d/inginious.conf`` file and apply the following rules:

  ::

    <VirtualHost *:80>
        ServerName my_inginious_domain
        LoadModule wsgi_module /usr/lib64/python3.5/site-packages/mod_wsgi/server/mod_wsgi-py35.cpython-35m-x86_64-linux-gnu.so

        WSGIScriptAlias / "/usr/bin/inginious-webapp"
        WSGIScriptReloading On

        Alias /static /usr/lib/python3.6/site-packages/inginious/frontend/static

        <Directory "/usr/bin">
            <Files "inginious-webapp">
                Require all granted
            </Files>
        </Directory>

        <DirectoryMatch "/usr/lib/python3.6/site-packages/inginious/frontend/static">
            Require all granted
        </DirectoryMatch>
    </VirtualHost>

    <VirtualHost *:8080>
        ServerName my_inginious_domain
        LoadModule wsgi_module /usr/lib64/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py35.cpython-35m-x86_64-linux-gnu.so

        WSGIScriptAlias / "/usr/bin/inginious-webdav"
        WSGIScriptReloading On

        <Directory "/usr/bin">
            <Files "inginious-webdav">
                Require all granted
            </Files>
        </Directory>
    </VirtualHost>

Please note that the compiled *wsgi* module path may differ according to the exact Python version you are running.


Using Apache on Ubuntu 18.04
````````````````````````````

Change the owner to the inginious folder and its contents to the Apache2 user:
::

    chown -R www-data:www-data /var/www/inginious

Set the global server name: add the line `ServerName localhost` in `/etc/apache2/conf.d/httpd.conf`

Set the environment variables used by the INGInious CLI scripts in the Apache service environment file, /etc/apache2/envvars :
::

    export INGINIOUS_WEBAPP_CONFIG="/var/www/inginious/configuration.yaml"
    export INGINIOUS_WEBAPP_HOST="0.0.0.0"
    export INGINIOUS_WEBAPP_PORT="80"

Add them also inside the file `/lib/systemd/system/apache2.service`, as follows:
::

    Environment=INGINIOUS_WEBAPP_CONFIG="/var/www/inginious/configuration.yaml"
    Environment=INGINIOUS_WEBAPP_HOST="0.0.0.0"
    Environment=INGINIOUS_WEBAPP_PORT="80"


Append this in your INGInious configuration.yaml

  ::

   local-config:
       tmp_dir: /var/www/inginious/agent_tmp

Add virtual host entries in a `/etc/apache2/sites-available/inginious.conf` file with the following rules:

  ::

    <VirtualHost *:80>
        WSGIScriptAlias / "/usr/local/bin/inginious-webapp"
        WSGIScriptReloading On

        Alias /static /usr/local/lib/python3.6/dist-packages/inginious/frontend/static

            <Directory "/usr/local/bin">
                <Files "inginious-webapp">
                    Require all granted
                </Files>
            </Directory>

            <DirectoryMatch "/usr/local/lib/python3.6/dist-packages/inginious/frontend/static">
                Require all granted
            </DirectoryMatch>

        ServerAdmin erelsgl@gmail.com
        DocumentRoot /var/www/inginious
    </VirtualHost>


    <VirtualHost *:8080>
            WSGIScriptAlias / "/usr/local/bin/inginious-webdav"
            WSGIScriptReloading On

            <Directory "/usr/local/bin">
                <Files "inginious-webdav">
                    Require all granted
                </Files>
            </Directory>
    </VirtualHost>

Please note that the static files path may differ according to the exact Python version you are running.

Then, enable the new site and reload apache2:

  ::

    a2enmod wsgi
    a2dissite 000-default
    a2ensite inginious
    systemctl reload apache2

Apache will automatically start the frontend.

To check that the various parts of the system are correctly installed, you can use the following commands.

1  Check that docker is active:

    # systemctl status docker

2  Check that mongo db is active:

    # systemctl status mongodb

3  Check that Apache 2 is active:

    # systemctl status apache2

All of them should be in status "active (running)".

4  Check that wsgi is installed:

    # source /etc/apache2/envvars
    # apache2 -M 

The last line should be "wsgi_module (shared)".

    # apache2 -S 

There should be two lines under `VirtualHost configuration:` referring to `inginious.conf`.

5  Check access to a file in the `static` folder, e.g.:

    # curl http://localhost/static/icons/wb.svg

6  Check access to the `courselist` folder:

    # curl http://localhost/courselist

7  Finally, open the URL to your website in a browser, and login as superadmin; you should see the INGInious homepage.

Optional apps
=============

.. _webdav_setup:

WebDAV setup
------------

An optional WebDAV server can be used with INGInious to allow course administrators to access
their course filesystem. This is an additional app that needs to be launched on another port or hostname.
Run the WebDAV server using :ref:`inginious-webdav`.

  ::

    inginious-webdav --config /path/to/configuration.yaml --port 8000

In your configuration file (see :ref:`ConfigReference`), set ``webdav_host`` to:
  ::

    <protocol>://<hostname>:<port>

where ``protocol`` is either ``http`` or ``https``, ``hostname`` and ``port`` the hostname and port
where the WebDAV app is running.

.. _webterm_setup:

Webterm setup
-------------

An optional web terminal can be used with INGInious to load the remote SSH debug session. This rely on an external tool.

To install this tool :
::

    $ git clone https://github.com/UCL-INGI/INGInious-xterm
    $ cd INGInious-xterm && npm install

You can then launch the tool by running:
::

    $ npm start bind_hostname bind_port debug_host:debug_ports

This will launch the app on ``http://bind_hostname:bind_port``. The ``debug_host`` and ``debug_ports`` parameters are
the debug paramaters on the local (see :ref:`ConfigReference`) or remote (see :ref:`inginious-agent-docker`) Docker agent.

To make the INGInious frontend aware of that application, update your configuration file by setting the ``webterm``
field to ``http://bind_hostname:bind_port`` (see :ref:`ConfigReference`).

For more information on this tool, please see `INGInious-xterm <https://github.com/UCL-INGI/INGInious-xterm>`_. Please
note that INGInious-xterm must be launched using SSL if the frontend is launched using SSL.
