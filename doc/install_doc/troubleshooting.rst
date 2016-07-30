Troubleshooting common problems
===============================

Solving problems hangs, on OS X with docker-machine or virtualbox to run Docker
-------------------------------------------------------------------------------

There is a known problem with Virtualbox shared folders: it is impossible for the VM to create a unix socket inside (for strange reasons).
To solve this, you can mount instead your `/Users` directory using `docker-machine-nfs`:

.. code:: base

    brew install docker-machine-nfs
    docker-machine-nfs default -f --nfs-config="-maproot=0"

