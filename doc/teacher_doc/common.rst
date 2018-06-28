Share common files between tasks
================================

Files stored in the subdirectory "$common" of a course are available to all tasks, inside the container, at the
path "/course/common". This directory is only mounted in the grading container.

Files stored in the subdirectory "$common/student" of a course are available to all tasks, inside the container, at the
path "/course/common/student". This directory is mounted in the grading container and in student containers.

All these folder are read-only inside a container.