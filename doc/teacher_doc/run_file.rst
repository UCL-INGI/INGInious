.. _run file:

Run file
========

When the student have submit his/her code, INGInious starts a new Docker container
with the right *environment* for the task (as given in the *.task* file). Inside this
container is launched a script, called *run*, that you have to provide in the
directory of your task.

Here is a simple example of a *run* file, compatible with the *default* environment,
that simply returns that the student's code is OK:
::

    #! /bin/bash
    feedback --result success

The *run* script is simply an executable application (a bash script, a python script, or
a compiled executable runnable by the container). INGInious' default containers provides
commands (also available as python libraries) to interact with the backend.

By default, the script is run inside the container in the /task directory, by a non-root
user. You can modify the container to change this (and everything else).

Usable commands in the *run* file
---------------------------------

feedback
````````

The *feedback* command allows you to set the result of your tests.
Every argument is optionnal.

-r, --result STATUS        set the result to STATUS. STATUS can be
                           success (the student succeeded the task),
                           failed (there are error in the student answer),
                           timeout (the tests timed out) or
                           crash (the tests crashed)
-f, --feedback MSG         set the feedback message to MSG. It is possible to set different
                           messages for each problems. You can use *-i* to change the problem
                           to which you assign the message
-i, --id PROBLEMID         set the problem id to which the message from the *-f* option is
                           assigned. Unused if *-f* is not set.

The *feedback* command can be called multiple times.

::

    feedback --result success --feedback "You're right, the answer is 42!"

getinput
````````

The *getinput* command returns the input given by the student for a specific problem id.
For example, for the problem id "pid", the command to do is:
::

    getinput pid

When a problem is defined with several boxes, the argument becomes *pid/bid* where "pid" stands for the problem id and "bid" for "box id".

parsetemplate
`````````````

The *parsetemplate* command injects the input given by the student in a template.
The command has this form:
::

    parsetemplate [-o|--output outputfile] template

where *template* is the file to parse. Output file is the destination file.
If the *-o* option is not given, the template will be replaced.

The markup in the templates is very simple: *@prefix@problemid@suffix@*.
Prefix allows to correct the indentation when needed (this is useful in Python).

Example of template file (in java)
::

    public class Main
    {
        public static void main(String[] args)
        {
    @        @problem_one@@
        }
    }

.. _run_student:

run_student
```````````

*run_student* allows the *run file* to start, at will, sub-containers. This makes you able to secure the grading, making sure the untrusted code
made by the student don't interact with yours.

run_student is fully configurable; you can change the container image (environment), set new timeouts, new memory limits, ... And you can call it as
many time as you want.

--container CONTAINER             Name of the container to use. The default is the same as the current container.
--time TIME                       Timeout (in CPU time) for the container. The default is the same as the current container.
--hard-time TIME                  Hard timeout for the container (in real time). The default is three times the value indicated for --time.
--memory MEMORY                   Maximum memory for the container, in Megabytes. The default is the same as the current container.
--share-network                   Share the network stack of the grading container with the student container. This is not the case by
                                  default. If the container container has network access, this will also be the case for the student!

Beyond these optionnals args, *run_student* also takes an additionnal (mandatory) arguments: the command to be run in the new container.

More technically, please note that:

- *run_student* proxies stdin, stdout, stderr, most signals and the return value
- There are special return values:
    - 252 means that the command was killed due to an out-of-memory
    - 253 means that the command timed out
    - 254 means that an error occured while running the proxy

archive
```````

*archive* allows you to put some data in an archive that will be returned to the frontend
and stored in the database for future reading. You can put there debug data, for example.

The command takes some arguments, which are all optionnal:

-o, --outsubdir    DIRECTORY        will put the file (specified with -a or -r)in the
                                    specified sub-directory in the output archive
-a, --add FILEPATH                  add the file to the archive
-r, --remove FILEPATH               remove the file from the archive