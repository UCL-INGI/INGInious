# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Task file managers """
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional


class AbstractTaskFileReader(object, metaclass=ABCMeta):
    """ Manages a type of task file """

    @abstractmethod
    def load(self, file_content) -> Dict[Any, Any]:
        """ Parses file_content and returns a dict describing a task """
        pass

    @abstractmethod
    def get_ext(self) -> str:
        """ Returns the task file extension. Must be @classmethod! """
        pass

    @abstractmethod
    def dump(self, descriptor: Dict[Any, Any]) -> Optional[str]:
        """ Dump descriptor and returns the content that should be written to the task file"""
        pass
