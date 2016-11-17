# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" RST task file manager. """

from inginious.common.task_file_readers.abstract_reader import AbstractTaskFileReader
from inginious.frontend.webapp.plugins.task_file_readers._dicttorst import dict2rst
from inginious.frontend.webapp.plugins.task_file_readers._rsttodict import rst2dict


class TaskRSTFileReader(AbstractTaskFileReader):
    """ Read and write task descriptions in restructuredText """

    def load(self, content):
        return rst2dict(content)

    @classmethod
    def get_ext(cls):
        return "rst"

    def dump(self, data):
        return dict2rst(data)


def init(plugin_manager, _, _2, _3):
    """
        Init the plugin. Configuration:
        ::

            plugins:
                - plugin_module: inginious.frontend.webapp.plugins.task_file_readers.rst_reader
    """

    plugin_manager.add_task_file_manager(TaskRSTFileReader())
