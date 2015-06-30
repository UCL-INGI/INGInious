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
""" A synchronized "layer" for JobManager """
import threading


class JobManagerSync(object):
    """ Runs job synchronously """

    def __init__(self, job_manager):
        self._job_manager = job_manager

    def new_job(self, task, inputdata, launcher_name="Unknown", debug=False):
        """
            Runs a new job.
            It works exactly like the JobManager class, instead that there is no callback and directly returns result.
        """
        job_semaphore = threading.Semaphore(0)

        def manage_output(job):
            """ Manages the output of this job """
            manage_output.job_return = job
            job_semaphore.release()

        self._job_manager.new_job(task, inputdata, manage_output, launcher_name, debug)
        job_semaphore.acquire()
        job_return = manage_output.job_return
        return job_return
