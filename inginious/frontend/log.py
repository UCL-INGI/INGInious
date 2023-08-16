# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import logging

def get_course_logger(coursename):
    """
    :param coursename: the course id
    :return: a logger object associated to a specific course
    """
    return logging.getLogger("inginious.course."+coursename)

def get_taskset_logger(coursename):
    """
    :param coursename: the course id
    :return: a logger object associated to a specific course
    """
    return logging.getLogger("inginious.course."+coursename)