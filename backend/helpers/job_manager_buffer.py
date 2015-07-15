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
""" Contains the JobManagerBuffer, which creates a buffer for a JobManager """

import uuid


class JobManagerBuffer(object):
    """ A buffer for a JobManager """

    def __init__(self, job_manager):
        self._job_manager = job_manager
        self._waiting_jobs = []
        self._jobs_done = {}

    def new_job(self, task, inputdata, launcher_name="Unknown", debug=False):
        """ Runs a new job. It works exactly like the JobManager class, instead that there is no callback """
        bjobid = uuid.uuid4()
        self._waiting_jobs.append(str(bjobid))
        self._job_manager.new_job(task, inputdata, lambda r: self._callback(bjobid, r), launcher_name, debug)
        return bjobid

    def _callback(self, bjobid, result):
        """ Callback for self._job_manager.new_job """
        self._jobs_done[str(bjobid)] = result
        self._waiting_jobs.remove(str(bjobid))

    def is_waiting(self, bjobid):
        """ Return true if the job is in queue """
        return str(bjobid) in self._waiting_jobs

    def is_done(self, bjobid):
        """ Return true if the job is done """
        return str(bjobid) in self._jobs_done

    def get_result(self, bjobid):
        """ Get the result of task. Must only be called ONCE, AFTER the task is done (after a successfull call to is_done). """
        result = self._jobs_done[str(bjobid)]
        del self._jobs_done[str(bjobid)]
        return result
