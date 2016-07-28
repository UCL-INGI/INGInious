Overriding system files
=======================

For some particular tasks (that involve networking), it may be necessary to overwrite/append to some system files,
such as `/etc/hosts` and `/etc/resolv.conf`. In order to do this, create a folder `systemfiles` in your task,
and create these files according to what you want to do:

`systemfiles/hosts`             the content of this file is append to the `/etc/hosts` of the container at start.
`systemfiles/resolv.conf`       the content of `/etc/resolv.conf` is replaced by the content of this file if it exists.

These files are also used in containers created by `run_student`.It is even possible to write dynamically on `systemfiles/xxx` while the
grading script is running, and new changes (made before `run_student`) will be set into the new container.

The grading container can also write directly on its `/etc/hosts` and `/etc/resolv.conf`, but it is discouradged as it will not be reflected in
student containers.