# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some type of exceptions used by parts of INGInious """


class CourseNotFoundException(Exception):
    pass


class CourseAlreadyExistsException(Exception):
    pass


class TasksetNotFoundException(Exception):
    pass


class TasksetUnreadableException(Exception):
    pass


class TasksetAlreadyExistsException(Exception):
    pass


class ImportTasksetException(Exception):
    pass
