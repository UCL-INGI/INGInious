.. _inginious-synchronize:

inginious-synchronize
=====================

Synchronization tool for INGInious Git repos. Each repository is suppposed to content the files required for a course.
When run, the tool pulls the modifications done remotely and force-merge the the local version if conflicts cannot be
resolved automatically.

A configuration file ``synchronize.json`` must be provided or specified using environment variable
``INGINIOUS_SYNC_CONFIG``. This file contains the main task directory as well as the course identifier, private key for
pulls and repo url, as follows:

::

    {
        "maindir":"../tasks",
        "repos":
        [
            {
                "course":"TEST0000",
                "keyfile":"TEST0000.key",
                "url":"git@github.com:user/TEST0000.git"
            },
            {
                "course":"TEST0001",
                "keyfile":"TEST0001.key",
                "url":"git@github.com:user/TEST0001.git"
            }
        ]
    }

For more compatibility, please run this command in an ``ssh-agent`` session.

Before adding in crontab, add the following lines to .ssh/config for user who runs the scripts :
::

    Host *
        StrictHostKeyChecking no

This tells SSH not to check host keys, we always trust the remote servers