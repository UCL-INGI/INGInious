Debugging tasks
===============

There are different ways to get more insight on what's going wrong with your tasks in case
of errors. Generally, those errors come from the fact the running environment may be different
from your task development environment (OS configuration, software set,...).

Debug information
-----------------
Every time an administrator submit a new job and receives result on the frontend, a *Debug information*
is made available in the sidebar. Those information contain all the submission metadata (input, result,
feedback,...) as well as the grading container standard output and standard error output.

Please note that every manipulation done with those streams will not be visible anymore in those information.
Redirected output won't be shown. This is important as spawning processes in non-shell oriented languages
will not redirect the spawned process standard output on the grading container standard output.

SSH debug
---------
Debugging tasks is made more easy using SSH debug feature. This aims at providing the same
user experience as local development. To make this feature work remotely
(regarding the INGInious Docker agent), please make sure you've correctly set up the debug
hosts and ports (see :ref:`ConfigReference` if needed).

Every administrator is able from the frontend to launch a debugging job. This is done by clicking
on the *>_* (left-chevron, underscore) button next to the *Submit* button. According to your
configuration, either a SSH command-line with auto-generated password will be given you (you will,
in this case, need an SSH client installed), or an embedded SSH console will pop up as the
feedback position.