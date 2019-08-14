Share common files between tasks
================================

Files stored in the subdirectory "$common" of a course are available to all tasks, inside the container, at the
path "/course/common". This directory is only mounted in the grading container.

Files stored in the subdirectory "$common/student" of a course are available to all tasks, inside the container, at the
path "/course/common/student". This directory is mounted in the grading container and in student containers.

All these folder are read-only inside a container.

Files stored in the subdirectory "$common/public" of a course are available to download from the frontend in each task. 
For example, if there is an image named “flower.png” that you need in all tasks, you will have to put it inside the 
folder “/path/to/INGInious/tasks/courseA/$common/public/”.

The image will then be available with the url: http://domain.name.com/course/courseA/$common/flower.png 