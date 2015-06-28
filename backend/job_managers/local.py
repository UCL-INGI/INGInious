# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Université Catholique de Louvain.
#
# This file is part of INGInious.
#
# INGInious is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INGInious is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
""" A JobManager that start an agent locally. This is the simplest way to start INGInious, but it only works on Linux machine where the backend
can access directly to docker and cgroups."""

from backend.job_managers.abstract import AbstractJobManager
from backend_agent.agent import LocalAgent


class LocalJobManager(AbstractJobManager):
    """ A Job Manager that starts and use a local agent """

    def __init__(self, image_aliases, agent_tmp_dir="./agent_tmp", hook_manager=None, is_testing=False, agent_class=LocalAgent):
        AbstractJobManager.__init__(self, image_aliases, hook_manager, is_testing)
        self._agent = agent_class(image_aliases, agent_tmp_dir)

    def start(self):
        pass

    def _execute_job(self, jobid, task, inputdata, debug):
        self._agent.new_job(jobid, task.get_course_id(), task.get_id(), inputdata, debug, None, lambda result: self._job_ended(jobid, result))

    def close(self):
        pass
