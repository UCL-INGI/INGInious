# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" YAML task file manager """
from typing import IO, Dict, Any, Optional

import inginious.common.custom_yaml
from inginious.common.task_file_readers.abstract_reader import AbstractTaskFileReader


class TaskYAMLFileReader(AbstractTaskFileReader):
    """ Read and write task descriptions in YAML """

    def load(self, content: IO) -> Dict[Any, Any]:
        return inginious.common.custom_yaml.load(content)

    @classmethod
    def get_ext(cls) -> str:
        return "yaml"

    def dump(self, data: Dict[Any, Any]) -> Optional[str]:
        return inginious.common.custom_yaml.dump(data)
