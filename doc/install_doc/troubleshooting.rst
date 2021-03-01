Troubleshooting common problems
===============================

Solving problems hangs, on OS X with docker-machine or VirtualBox to run Docker
-------------------------------------------------------------------------------

There is a known problem with VirtualBox shared folders: it is impossible for the VM to create a unix socket inside (for strange reasons).
To solve this, you can mount instead your `/Users` directory using ``docker-machine-nfs``:

.. code:: base

    brew install docker-machine-nfs
    docker-machine-nfs default -f --nfs-config="-maproot=0"

LTI grades are not pushed back using LetsEncrypt
------------------------------------------------

INGInious uses PyLTI which uses oauth, oauth2 and libhttp2. The list of certificate authorities known to libhttp2
may be out of day with your host operating system. In particular, as of August 2016, it does not
include the LetsEncrypt CA, and thus websites protected with a LetsEncrypt certificate won't work
(you won't be able to push grades back).

LTI frontend keeps on OAuth errors
----------------------------------

LTI uses OAuth which uses time-based replay prevention. You need to insure that your webserver (LTI consumer) and LTI
producer have reasonably synchronous clocks.

Impossible to get the LTI frontend work
---------------------------------------

You may find the `saLTIre <https://saltire.lti.app/>` tool  useful when debugging
producers and consumers.

It is impossible to modify the course.yaml from the webdav interface
--------------------------------------------------------------------

Some editors/webdav clients attempt to first move/delete a file before modifying it.
It is forbidden to remove or rename the course.yaml, so the modification will fail.

Use simpler editors (such as nano/vim) that directly edit the file rather than doing strange things.