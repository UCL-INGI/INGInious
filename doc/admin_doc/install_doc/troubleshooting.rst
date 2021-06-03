Troubleshooting common problems
===============================

LTI-related issues
------------------

You may experience issues when the external platform authentication to INGInious: two main kinds of issues
can occur, according to the error message you get when accessing the INGInious task.

Error while parsing the LTI request
`````````````````````````````````````

In this case, the authentication message sent by the external platform is probably erroneous.
You can check your INGInious setup by using the saLTIre_ app:

#. Choose the *Test Platform* tool.
#. In the *Security Model* tab, specify the Message (LTI) URL of your INGInious task, and
   the course consumer key and shared secret.
#. In the top-bar, click on *Save*.
#. In the top-bar, in the *Connect* dropdown menu, you can *Preview connection* and see the POST request
   that will be done by the external app to INGInious.
#. Click on *Connect* to open the INGInious task in a new window or iframe. Both methods are supported.
#. If this error message appears, there are chances the POST request has been altered. The POST message
   is displayed in your INGInious logs.

If everything looks fine though, eventually check your webserver configuration to ensure that all the POST
request headers are transferred to the app.

Couldn't validate LTI request
```````````````````````````````

In this case, the authentication message sent by the external platform is syntaxically correct. However, the
authentication information provided is probably erroneous. The LTI interface relies on OAuth to perform the
authentication. There are two main reasons leading to this issue :

* The request has expired. This is a time-based replay prevention: authentication should perform in a short
  window of time. Check that both servers are approximately set to the same **universal time**
  (double-check for timezone config errors). If you do not administrate the external platform, simply
  check your INGInious server and test your setup using saLTIre_ (see above).
* The OAuth signature sent by the external app and computed by INGInious do not match. The OAuth signature is
  a hash computed using the request URL, the LTI consumer key and shared secret. Check the consumer and shared
  secret on both side and ensure they are correct (no trailing spaces, ...). If the problem persists, check your
  webserver configuration to ensure there is no URL rewrite performed before transferring the request to the app.
  This includes : http/https redirection scheme, domain aliases, ...

.. _saLTIre: https://saltire.lti.app/

Scores are not pushed back
```````````````````````````

The list of certificate authorities known to libhttp2
may be out of day with your host operating system. In particular, as of August 2016, it does not
include the LetsEncrypt CA, and thus websites protected with a LetsEncrypt certificate won't work
(you won't be able to push grades back).

Solving problems hangs, on OS X with docker-machine or VirtualBox to run Docker
-------------------------------------------------------------------------------

There is a known problem with VirtualBox shared folders: it is impossible for the VM to create a unix socket inside (for strange reasons).
To solve this, you can mount instead your `/Users` directory using ``docker-machine-nfs``:

.. code:: bash

    brew install docker-machine-nfs
    docker-machine-nfs default -f --nfs-config="-maproot=0"

It is impossible to modify the course.yaml from the webdav interface
--------------------------------------------------------------------

Some editors/webdav clients attempt to first move/delete a file before modifying it.
It is forbidden to remove or rename the course.yaml, so the modification will fail.

Use simpler editors (such as nano/vim) that directly edit the file rather than doing strange things.