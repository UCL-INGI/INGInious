Batch containers
================

Batch containers are a specific type of containers that make "batch" operations on courses.
They can take as input all the submissions of a course and do, for example, a detection of plagiarism among all the students.

Batch containers do very specific actions and sometimes are made for a specific course. **In order to create a new batch container, make sure you
tried before to create a standard (grading) container for INGInious (see :doc:`create_container`)**.

Input, output, and metadata
---------------------------

A batch container is fully described by its metadata. The metadata of the container image contains its title, description, and its arguments.

An argument is itself composed of a ```key```, a ```name```, a ```path``` and a ```type```. For starting a batch job, the user has to fill in all the
arguments, that will be mounted in the container in the folder ```/input/path```, where ```path``` is the one you indicated to describe the argument.
The ```name``` part of the argument is only used for displaying, and the ```key``` is used for internal purposes only (besides a little exception,
see below)

There are two types of arguments: ```file``` and ```text```. As you can guess, the difference is simply that while the ```file``` type take a file
as input, ```text``` takes a single line of text. Both (even ```text```) are still mounted in the folder ```/input/...``` as said earlier.

The return value of a working batch container script should always be 0. In this case, the content of the ```/output/``` will be stored in the
database and made available for the staff of the course.

Taking course data and submissions as input
-------------------------------------------

In order to receive the course data (the content of the folder of the course) and/or all the submissions made from the course, you simply have to
create an argument with type ```file``` and ```key``` respectively equal to ```course``` or ```submissions```.

The file mounted on the given path will then be a ```.tar.gz``` archive.

Indicating metadata in the Dockerfile
-------------------------------------

Here is an example of how to include metadata in the Dockerfile:

::

    # This container is a batch one
    LABEL org.inginious.batch=1

    #
    # Some Metadata for the container
    #
    LABEL org.inginious.batch.title="Test Batch Container"
    LABEL org.inginious.batch.description="A simple test backend container that put a simple website in its results."

    # Course files
    LABEL org.inginious.batch.args.course=file
    LABEL org.inginious.batch.args.course.name="Course"
    LABEL org.inginious.batch.args.course.path="course.tgz"
    LABEL org.inginious.batch.args.course.description="The course files"

    # Submissions
    LABEL org.inginious.batch.args.submissions=file
    LABEL org.inginious.batch.args.submissions.name="Submissions"
    LABEL org.inginious.batch.args.submissions.path="submissions.tgz"
    LABEL org.inginious.batch.args.submissions.description="All submissions made by students"

    # Text
    LABEL org.inginious.batch.args.text=text
    LABEL org.inginious.batch.args.text.path="text.txt"
    LABEL org.inginious.batch.args.text.name="A simple text field"
    LABEL org.inginious.batch.args.text.description="Please enter something here (won't be used at all)"

    # And a file
    LABEL org.inginious.batch.args.file=file
    LABEL org.inginious.batch.args.file.path="yourfile"
    LABEL org.inginious.batch.args.file.name="Submit a file here"
    LABEL org.inginious.batch.args.file.description="This file will be made available in the results as 'yourfile'"

As you can see:

- All batch containers must have a line ```LABEL org.inginious.batch=1``` in their Dockerfile
- Args types are indicated via the lines ```LABEL org.inginious.batch.args.KEY=TYPE```, where ```KEY``` and ```TYPE``` are of course the type and
the key name of the argument.
- Args names are indicated via the lines ```LABEL org.inginious.batch.args.KEY.name="THE NAME"```
- Args path are indicated via the lines ```LABEL org.inginious.batch.args.KEY.path="THE/PATH/INSIDE/SLASH/INPUT"```
- Args descriptions are indicated via the lines ```LABEL org.inginious.batch.args.KEY.description="THE DESCRIPTION"```

Example
-------

A working example of full-featured batch container is available here: https://github.com/UCL-INGI/INGInious-containers/tree/master/batch/test
