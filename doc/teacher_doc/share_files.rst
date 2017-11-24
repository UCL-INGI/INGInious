Allowing students to download files
===================================

Files stored in the subdirectory "public" of a task are available to download from the
frontend.

For example, if you have a course with course id "courseA", and a task with task id "taskB",
and if you want to distribute an image named "flower.png", you will have to put it inside
the folder "/path/to/INGInious/tasks/courseA/taskB/public/".

The image will then be available with the url:
http://domain.name.com/course/courseA/taskB/flower.png

This allows you to insert images inside the context of your tasks, and to share
additional resources like datasets or slides.

.. DANGER::
    The files stored in your public folder will be available to all users, without authentication needed.
