# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Some type of exceptions used by parts of INGInious """


class InvalidNameException(Exception):
    pass


class TaskNotFoundException(Exception):
    pass


class TaskAlreadyExistsException(Exception):
    pass


class TaskUnreadableException(Exception):
    pass


class TaskReaderNotFoundException(Exception):
    pass
