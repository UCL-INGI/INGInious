# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

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
